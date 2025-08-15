import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import time
import json
import os
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class GuangdongTaxScraper:
    """广东省税务局最新文件爬虫 - 增强版（含内容抓取）"""

    def __init__(self, save_dir="税务文件"):
        """
        初始化爬虫
        :param save_dir: 保存文件的目录名
        """
        self.base_url = "https://guangdong.chinatax.gov.cn"
        self.target_url = "https://guangdong.chinatax.gov.cn/gdsw/zxwj/zxwj.shtml"
        self.save_dir = save_dir
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://guangdong.chinatax.gov.cn/',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.lock = threading.Lock()  # 用于线程安全的文件操作

        # 创建保存目录
        self.create_save_directory()

    def create_save_directory(self):
        """创建保存文件的目录结构"""
        # 主目录
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            print(f"创建目录: {self.save_dir}")

        # 创建子目录
        self.text_dir = os.path.join(self.save_dir, "文件内容")
        self.summary_dir = os.path.join(self.save_dir, "汇总信息")

        for dir_path in [self.text_dir, self.summary_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

    def clean_filename(self, filename):
        """
        清理文件名，移除非法字符
        :param filename: 原始文件名
        :return: 清理后的文件名
        """
        # 移除或替换Windows文件名中的非法字符
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in illegal_chars:
            filename = filename.replace(char, '_')

        # 限制文件名长度（Windows限制）
        if len(filename) > 200:
            filename = filename[:200]

        # 移除首尾空格
        filename = filename.strip()

        return filename

    def parse_html_content(self, html_content):
        """
        解析HTML内容，提取税务文件信息
        :param html_content: HTML内容字符串
        :return: 提取的数据列表
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        data = []

        # 查找包含文件列表的div
        file_list = soup.find('div', {'id': 'ajaxlist'})
        if not file_list:
            file_list = soup.find('div', class_='fileList')

        if file_list:
            # 查找所有包含公告信息的li标签
            items = file_list.find_all('li', class_='itm')

            for item in items:
                try:
                    record = self.extract_item_data(item)
                    if record:
                        data.append(record)
                except Exception as e:
                    print(f"解析条目时出错: {e}")
                    continue

            # 处理特殊的li标签（class="none"）
            none_items = file_list.find_all('li', class_='none')
            for item in none_items:
                try:
                    record = self.extract_item_data(item)
                    if record:
                        data.append(record)
                except Exception as e:
                    print(f"解析特殊条目时出错: {e}")
                    continue
        else:
            print("未找到文件列表容器")

        return data

    def extract_item_data(self, item):
        """
        从单个li元素中提取数据
        :param item: BeautifulSoup元素对象
        :return: 提取的数据字典
        """
        h4_tag = item.find('h4')
        if not h4_tag:
            return None

        a_tag = h4_tag.find('a')
        if not a_tag:
            return None

        # 获取标题
        title = a_tag.get('title', '').strip()
        if not title:
            font_tag = a_tag.find('font')
            if font_tag:
                title = font_tag.get_text(strip=True)
            else:
                title = a_tag.get_text(strip=True)

        # 获取链接
        href = a_tag.get('href', '')
        if not href:
            return None

        # 构建完整链接
        if href.startswith('http'):
            full_url = href
        elif href.startswith('/'):
            full_url = self.base_url + href
        else:
            full_url = urljoin(self.target_url, href)

        # 获取发布时间
        time_span = h4_tag.find('span', class_='time')
        publish_time = ''
        if time_span:
            publish_time = time_span.get_text(strip=True).replace('[', '').replace(']', '')

        # 检查是否有文件解读图标
        has_interpretation = False
        em_tag = h4_tag.find('em', class_='wjjdIcon')
        if em_tag:
            style = em_tag.get('style', '')
            if 'visibility: visible' in style or (style and 'display: none' not in style):
                has_interpretation = True
            elif not style:
                has_interpretation = True

        # 从URL中提取文档ID
        doc_id = ''
        if 'content_' in href:
            try:
                doc_id = href.split('content_')[1].split('.')[0]
            except:
                pass

        return {
            '标题': title,
            '相对链接': href,
            '完整链接': full_url,
            '发布时间': publish_time,
            '有文件解读': has_interpretation,
            '文档ID': doc_id
        }

    def fetch_page(self, url=None, max_retries=3):
        """
        获取网页内容，支持重试机制
        :param url: 目标URL
        :param max_retries: 最大重试次数
        :return: 网页HTML内容
        """
        if url is None:
            url = self.target_url

        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()

                # 自动检测编码
                response.encoding = response.apparent_encoding
                if response.encoding is None or response.encoding == 'ISO-8859-1':
                    response.encoding = 'utf-8'

                return response.text

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(2)
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2)

        return None

    def extract_article_content(self, html_content, url):
        """
        从文章页面提取正文内容
        :param html_content: 文章页面的HTML内容
        :param url: 文章URL（用于调试）
        :return: 提取的文本内容
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        content_parts = []

        # 策略1: 查找文章主体容器
        article_containers = [
            soup.find('div', class_='article-content'),
            soup.find('div', class_='content'),
            soup.find('div', class_='main-content'),
            soup.find('div', class_='text'),
            soup.find('div', class_='zwxl'),  # 正文内容
            soup.find('div', class_='TRS_Editor'),  # TRS编辑器内容
            soup.find('div', class_='Custom_UnionStyle'),  # 自定义样式内容
            soup.find('div', id='zoom'),  # 缩放内容区
            soup.find('div', class_='view'),  # 查看区域
            soup.find('article'),  # HTML5 article标签
            soup.find('main'),  # HTML5 main标签
        ]

        # 找到第一个存在的容器
        main_content = None
        for container in article_containers:
            if container:
                main_content = container
                break

        # 如果找不到特定容器，尝试查找包含大量文本的div
        if not main_content:
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text(strip=True)
                # 查找包含较多文字的div（至少200个字符）
                if len(text) > 200 and not div.find_parent('script'):
                    # 检查是否包含典型的正文关键词
                    keywords = ['第一条', '第二条', '第一章', '为了', '根据', '按照', '通知', '公告', '规定']
                    if any(keyword in text for keyword in keywords):
                        main_content = div
                        break

        if main_content:
            # 提取标题（如果有）
            title_tags = soup.find_all(['h1', 'h2', 'h3'])
            for title_tag in title_tags:
                title_text = title_tag.get_text(strip=True)
                if title_text and len(title_text) > 5:
                    content_parts.append(f"【标题】{title_text}\n")
                    break

            # 提取发布信息
            pub_info = soup.find('div', class_='info') or soup.find('div', class_='article-info')
            if pub_info:
                pub_text = pub_info.get_text(strip=True)
                if pub_text:
                    content_parts.append(f"【发布信息】{pub_text}\n")

            content_parts.append("\n【正文内容】\n")

            # 提取所有段落文本
            paragraphs = main_content.find_all(['p', 'div', 'span'])

            for element in paragraphs:
                # 跳过脚本和样式
                if element.name in ['script', 'style']:
                    continue

                # 获取直接文本内容（不包括子元素的文本）
                text = element.get_text(strip=True)

                # 过滤掉太短的文本
                if text and len(text) > 5:
                    # 检查是否是重复内容
                    if text not in content_parts:
                        content_parts.append(text)

            # 如果段落提取失败，使用全文本
            if len(content_parts) < 5:
                full_text = main_content.get_text(separator='\n', strip=True)
                content_parts = [full_text]

        else:
            # 降级策略：提取整个body的文本
            body = soup.find('body')
            if body:
                # 移除script和style标签
                for script in body(['script', 'style']):
                    script.decompose()

                full_text = body.get_text(separator='\n', strip=True)
                # 清理多余的空行
                lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                content_parts = lines

        # 合并内容
        final_content = '\n'.join(content_parts)

        # 清理内容
        final_content = self.clean_text_content(final_content)

        return final_content

    def clean_text_content(self, text):
        """
        清理提取的文本内容
        :param text: 原始文本
        :return: 清理后的文本
        """
        # 移除多余的空白行
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:
                # 移除多余的空格
                line = ' '.join(line.split())
                cleaned_lines.append(line)

        # 合并连续的空行
        final_lines = []
        prev_empty = False

        for line in cleaned_lines:
            if not line:
                if not prev_empty:
                    final_lines.append('')
                    prev_empty = True
            else:
                final_lines.append(line)
                prev_empty = False

        return '\n'.join(final_lines)

    def fetch_and_save_article(self, item, index, total):
        """
        获取并保存单篇文章内容
        :param item: 文章信息字典
        :param index: 当前索引
        :param total: 总数
        :return: 成功与否
        """
        title = item['标题']
        url = item['完整链接']

        print(f"\n[{index}/{total}] 正在处理: {title[:50]}...")

        # 获取文章页面
        html_content = self.fetch_page(url, max_retries=2)
        if not html_content:
            print(f"  ✗ 无法获取页面内容")
            return False

        # 提取文章内容
        article_content = self.extract_article_content(html_content, url)

        if not article_content or len(article_content) < 50:
            print(f"  ✗ 提取内容失败或内容太少")
            return False

        # 生成文件名
        clean_title = self.clean_filename(title)
        if item['发布时间']:
            filename = f"{item['发布时间']}_{clean_title}.txt"
        else:
            filename = f"{clean_title}.txt"

        filepath = os.path.join(self.text_dir, filename)

        # 保存文件
        try:
            with self.lock:
                with open(filepath, 'w', encoding='utf-8') as f:
                    # 写入元信息
                    f.write(f"标题: {title}\n")
                    f.write(f"链接: {url}\n")
                    f.write(f"发布时间: {item['发布时间']}\n")
                    f.write(f"是否有文件解读: {'是' if item['有文件解读'] else '否'}\n")
                    f.write("=" * 80 + "\n\n")

                    # 写入正文内容
                    f.write(article_content)

            print(f"  ✓ 保存成功: {filename}")
            return True

        except Exception as e:
            print(f"  ✗ 保存失败: {e}")
            return False

    def batch_fetch_articles(self, data, max_workers=5):
        """
        批量获取所有文章内容
        :param data: 文章列表数据
        :param max_workers: 最大并发数
        :return: 统计信息
        """
        total = len(data)
        success_count = 0
        failed_items = []

        print(f"\n开始批量获取 {total} 篇文章内容...")
        print(f"使用 {max_workers} 个并发连接")
        print("=" * 60)

        # 使用线程池并发下载
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_item = {}
            for i, item in enumerate(data, 1):
                future = executor.submit(self.fetch_and_save_article, item, i, total)
                future_to_item[future] = item

                # 控制提交速度，避免过快
                if i % 10 == 0:
                    time.sleep(1)

            # 处理完成的任务
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                    else:
                        failed_items.append(item['标题'])
                except Exception as e:
                    print(f"处理出错: {e}")
                    failed_items.append(item['标题'])

        # 显示统计信息
        print("\n" + "=" * 60)
        print(f"批量下载完成！")
        print(f"成功: {success_count}/{total}")
        print(f"失败: {len(failed_items)}/{total}")

        if failed_items:
            print("\n失败的文章:")
            for title in failed_items[:10]:  # 只显示前10个
                print(f"  - {title}")
            if len(failed_items) > 10:
                print(f"  ... 还有 {len(failed_items) - 10} 个")

        return {
            'total': total,
            'success': success_count,
            'failed': len(failed_items),
            'failed_items': failed_items
        }

    def save_summary(self, data, stats):
        """
        保存汇总信息
        :param data: 文章数据列表
        :param stats: 统计信息
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存Excel汇总
        excel_file = os.path.join(self.summary_dir, f'文件清单_{timestamp}.xlsx')
        df = pd.DataFrame(data)

        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='文件清单')

            # 添加统计信息sheet
            stats_df = pd.DataFrame([stats])
            stats_df.to_excel(writer, index=False, sheet_name='下载统计')

        print(f"\n汇总信息已保存到: {excel_file}")

        # 保存下载日志
        log_file = os.path.join(self.summary_dir, f'下载日志_{timestamp}.txt')
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"广东省税务局文件下载日志\n")
            f.write(f"下载时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=" * 60 + "\n")
            f.write(f"总文件数: {stats['total']}\n")
            f.write(f"成功下载: {stats['success']}\n")
            f.write(f"下载失败: {stats['failed']}\n")
            f.write(f"=" * 60 + "\n")

            if stats['failed_items']:
                f.write("\n失败文件列表:\n")
                for item in stats['failed_items']:
                    f.write(f"  - {item}\n")

        print(f"下载日志已保存到: {log_file}")

    def run(self, fetch_content=True, max_workers=5):
        """
        运行爬虫主程序
        :param fetch_content: 是否获取文章内容
        :param max_workers: 最大并发数
        :return: 提取的数据列表
        """
        print("\n" + "=" * 60)
        print("广东省税务局文件下载器")
        print("目标网址:", self.target_url)
        print("保存目录:", os.path.abspath(self.save_dir))
        print("=" * 60 + "\n")

        # 获取文件列表页面
        print("正在获取文件列表...")
        html_content = self.fetch_page()
        if not html_content:
            print("无法获取网页内容，程序终止")
            return []

        # 解析文件列表
        print("正在解析页面内容...")
        data = self.parse_html_content(html_content)

        if not data:
            print("未能提取到数据")
            return []

        print(f"成功提取 {len(data)} 个文件信息")

        # 是否获取文章内容
        if fetch_content:
            stats = self.batch_fetch_articles(data, max_workers)
            self.save_summary(data, stats)
        else:
            # 仅保存列表信息
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            excel_file = os.path.join(self.summary_dir, f'文件清单_{timestamp}.xlsx')
            df = pd.DataFrame(data)
            df.to_excel(excel_file, index=False)
            print(f"\n文件清单已保存到: {excel_file}")

        return data


def main():
    """主函数"""
    # 创建爬虫实例
    scraper = GuangdongTaxScraper(save_dir="广东税务文件")

    # 运行爬虫
    # fetch_content=True 表示下载文章内容
    # max_workers 控制并发数，建议不要设置太高，避免对服务器造成压力
    data = scraper.run(fetch_content=True, max_workers=3)

    if data:
        print(f"\n程序执行完成！")
        print(f"所有文件已保存到: {os.path.abspath(scraper.save_dir)}")
        print(f"  - 文件内容目录: {os.path.abspath(scraper.text_dir)}")
        print(f"  - 汇总信息目录: {os.path.abspath(scraper.summary_dir)}")


if __name__ == "__main__":
    main()