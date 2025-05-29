import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
import os
from pypinyin import lazy_pinyin
from datetime import datetime
from .common import detect_file_encoding, replace_roman_with_chinese

from .Pinyin_Processor import pinyin_process
import warnings 
# import subprocess

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)


# current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

class EpubProcessor:
    """
    处理EPUB文件的类，包含多种方法，如epub->txt，txt->长短句，txt和长短句->rime
    """
    def __init__(self, input_path, output_path, output_files, current_time, is_web=False):
        """初始化处理器
        Args:
            input_path: EPUB文件本身的路径
            output_path: 输出文件路径，这是路径也就是文件夹，不是文件
            output_files: 输出文件路径，这是txt文件们：原版、短句、长句
            is_web: 是否是通过Web界面调用
        """
        self.input_path = input_path # 这是EPUB文件本身的路径 .replace('\\', '/') 
        self.output_path = output_path # 这是路径也就是文件夹，不是文件  .replace('\\', '/')
        self.output_files = output_files # 这是txt文件们：原版、短句、长句
        self.content = ""
        self.processed_content = []
        self.current_time = current_time
        self.is_web = is_web
        self.web_output_files = []  # 用于收集需要在Web界面下载的文件
    def read_epub(self):
        """从EPUB文件中读取内容"""
        tmp=''
        book = epub.read_epub(self.input_path)
        # for item in book.get_items():
        #     if item.get_type() == ebooklib.ITEM_DOCUMENT:
        #         # self.content += item.get_body_content().decode('utf-8')
        #         content = item.get_body_content().decode('utf-8')
    
    # def extract_sections(self):
        # """提取所有章节内容"""
                # sections = re.findall(r'<.*id=\"CHP.*?>.*</.*?>',content, re.DOTALL)
                
                # for section in sections:
                #     tmp+=section
                #     tmp+='\n'
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_body_content().decode('utf-8')
                tmp += content
                tmp += '\n'
        print(f"总长度: {len(tmp)}")
        
        return tmp
    
    def process_html(self, html_content):
        """处理HTML内容，提取特定标签
        
        注意：此函数已弃用，推荐直接使用 clean_html(html_content) 来处理HTML内容，
        这样可以避免不必要的中间步骤和重复解析。
        保留此函数仅为向后兼容性。
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取h3标签,标题（金匮要略格式）
        h3_tags = soup.find_all('div', class_='h3', id=re.compile(r'CHP\d+'))
        for tag in h3_tags:
            self.processed_content.append(str(tag))
        
        # 提取h2标签,标题（中医临床必读丛书20册格式）
        h2_tags = soup.find_all('h2', id=re.compile(r'CHP\d+'))
        for tag in h2_tags:
            self.processed_content.append(str(tag))

        # 提取h4标签,标题（中医临床必读丛书20册格式）
        h4_tags = soup.find_all('h4', id=re.compile(r'CHP\d+'))
        for tag in h4_tags:
            self.processed_content.append(str(tag))
        
        # 提取内容段落（金匮要略格式）
        p_tags = soup.find_all('div', class_='pCls')
        for tag in p_tags:
            self.processed_content.append(str(tag))

        # 提取内容段落，所有的p标签
        # 伤寒论设计的p标签的class_：
        # 1. chapterTitle
        # 2. sectionTitle
        # 3. content
        # 4. postil
        # 5. center-content
        # 6. zs
        content_tags = soup.find_all('p')
        for tag in content_tags:
            self.processed_content.append(str(tag))

        content_tags = soup.find_all('span')
        for tag in content_tags:
            self.processed_content.append(str(tag))

    
    def clean_html(self, html_content=None):
        """清理HTML标签，只保留文本内容
        Args:
            html_content: 可选的HTML内容，如果提供则直接处理，否则使用processed_content
        """
        if html_content is not None:
            # 直接处理传入的HTML内容，去掉所有HTML标签
            soup = BeautifulSoup(html_content, 'html.parser')
            # 使用get_text()方法直接提取所有文本内容，自动去掉所有HTML标签
            final_content = soup.get_text(separator='\n', strip=True)
        else:
            # 使用原有的processed_content处理方式（向后兼容）
            final_soup = BeautifulSoup('\n'.join(self.processed_content), 'html.parser')
            final_content = final_soup.get_text(separator='\n', strip=True)
        
        # 统一的文本清理
        final_content = final_content.replace('　','')
        final_content = final_content.replace('1\n2','')
        final_content = final_content.replace('\n\n\n','\n')
        final_content = final_content.replace('\n\n ','\n')
        final_content = final_content.replace('        ','')

        return final_content
    
    def save_output(self, content):
        """保存处理结果到文件"""
        txt_file = os.path.join(self.output_path, f"epub转txt_{self.current_time}.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(content)
        if self.is_web:
            self.web_output_files.append(txt_file)
        return txt_file

    def split_into_short_sentences(self, input_path, output_dir):
        # 添加时间戳到输出文件名
        output_path = f"{os.path.splitext(output_dir)[0]}_{self.current_time}{os.path.splitext(output_dir)[1]}"
        
        # 读取清理后的内容
        epub_txt_file = input_path
        with open(epub_txt_file, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # 拆分短句
        split_content = re.split(r'[，。！？；：、\s\n]+', file_content)
        
        # 保存结果
        with open(output_path, 'w', encoding='utf-8') as output_file:
            for item in split_content:
                if item:  # 避免写入空字符串
                    output_file.write(item + '\n')
        
        if self.is_web:
            self.web_output_files.append(output_path)
        
        return output_path
    
    # 长句不需要删除标点，输出时依然需要输出标点，如
    # ✅上四味，以水八升，先煮蜀漆、麻黄，
    # ❌上四味以水八升先煮蜀漆麻黄

    def split_into_long_sentences(self, input_path, output_dir):
        """将内容拆分成无标点的长句
        Args:
            output_path: 输出文件路径
        """
        # 添加时间戳到输出文件名
        output_path = f"{os.path.splitext(output_dir)[0]}_{self.current_time}{os.path.splitext(output_dir)[1]}"
        
        # 读取清理后的内容
        epub_txt_file = input_path
        with open(epub_txt_file, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # 保存结果
        with open(output_path, 'w', encoding='utf-8') as output_file:
            
            # output_file.write(
            #     "# 生成工具 https://github.com/whitewatercn/rimetool\n" +
            #     "# 生成时间 " + current_time + "\n" +
            #     "---\n"
            # )
            for item in file_content.split('\n'):
                if item:  # 避免写入空字符串
                    cleaned_item = item
                    output_file.write(cleaned_item + '\n')
        
        if self.is_web:
            self.web_output_files.append(output_path)
        
        return output_path

    def to_rime(self, input_file, output_name):
        """txt->rime
        Args:
            input_file: 输入文件路径
            output_name: 输出文件名（不含扩展名）
        """
        output_file = os.path.join(self.output_path, f'{output_name}.dict.yaml')
        encoding = detect_file_encoding(input_file)

        with open(input_file, 'r', encoding=encoding) as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            outfile.write(
                "# 生成工具 https://github.com/whitewatercn/rimetool\n" +
                "# 生成时间 " + self.current_time + "\n" +
                "---\n"
            )
            # 处理每一行
            for line in infile:
                content = line.strip()
                if not content:  # 跳过空行
                    continue
                if content.startswith('#') or content == '---':
                    outfile.write(f"{content}\n")
                else:
                    # 将罗马数字转换为中文数字
                    content = replace_roman_with_chinese(content)
                    # 删除所有的 '-'
                    content = content.replace('-', '')
                    pinyin = ''
                    # 生成拼音
                    pinyin = pinyin.join(pinyin_process(content))
                    # 写入rime格式
                    outfile.write(f"{content}\t{pinyin}\t1\n")
        
        print(f"已生成rime格式文件: {os.path.abspath(output_file)}")
        
        if self.is_web:
            self.web_output_files.append(output_file)
        
        return output_file
    
    
    def epub_to_rime(self, output_files):
        """
        一键直达 epub->rime
        """
        input_path = self.epub_to_txt()
        result_files = self.txt_to_rime_all(input_path, output_files)
        
        if self.is_web:
            return self.web_output_files
        return result_files

    def txt_to_rime_all(self, input_path, output_files):
        """
        一键直达 txt->长短句的rime
        """
        short_path = self.txt_to_short_long(input_path, output_files)
        rime_files = self.txt_short_long_to_rime(output_files)
        
        if self.is_web:
            return self.web_output_files
        return rime_files


    def epub_to_txt(self):
        """
        第一个部分: epub->txt，简单地读取epub文件，转成一个没有各种标签（img，h1等）的txt文件
        """
        print("\n*** 第一部分: epub->txt ***\n")
        # 第一步：读取EPUB文件并处理格式
        print("读取EPUB文件...")
        try:
            html_content = self.read_epub()
            print(f"EPUB文件读取成功，内容长度: {len(html_content)}")
        except Exception as e:
            print(f"读取EPUB文件失败: {e}")
            return None
        
        print("处理HTML内容并清理标签...")
        # 直接将read_epub的结果传递给clean_html，跳过process_html步骤
        final_content = self.clean_html(html_content)
        
        print("保存结果...")
        self.content = final_content
        output_file = self.save_output(final_content)
        
        print(f"epub->txt 处理完成！结果已保存到: {output_file}")
        return output_file

    def txt_to_short_long(self, input_path, output_files):
        """
        第二个部分: 将txt文件转成短词组和长词组词库
        """
        print("\n*** 第二部分: 将txt文件转成短词组和长词组词库 ***\n")
        # 第二步：执行短句拆分
        print("开始短句拆分...")
        short_path = self.split_into_short_sentences(input_path, output_files['short'])
        print(f"短句拆分完成，结果保存在: {output_files['short']}")

        # 第三步：执行长句拆分
        print("开始长句拆分...")
        long_path = self.split_into_long_sentences(input_path, output_files['long'])
        print(f"长句拆分完成，结果保存在: {output_files['long']}")
        
        result = [short_path, long_path]
        if self.is_web:
            return result
        return result

    def txt_short_long_to_rime(self, output_files):
        """
        第三个部分: 将txt原版、短词组、长词组词库转成rime格式
        """
        print("\n*** 第三部分: 将txt原版、短词组、长词组词库转成rime格式***\n")
        print("开始生成rime格式文件...")
        
        output_short_time = f"{os.path.splitext(output_files['short'])[0]}_{self.current_time}{os.path.splitext(output_files['short'])[1]}"
        output_long_time = f"{os.path.splitext(output_files['long'])[0]}_{self.current_time}{os.path.splitext(output_files['long'])[1]}"
        
        short_rime = self.to_rime(output_short_time, "short_rime"+self.current_time)
        long_rime = self.to_rime(output_long_time, "long_rime"+self.current_time)
        
        result = [short_rime, long_rime]
        if self.is_web:
            return result
        return result

    def replace_pinyin(self, input_path, output_path):
        return
        """替换拼音，只将"俞"字对应的"yu"替换为"shu"，其他位置的"yu"保持不变"""
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
            # 替换俞的拼音
            for line in infile:
                parts = line.strip().split('\t')
                if len(parts) == 3:
                    sentence, pinyin_str, label = parts
                    modified_pinyin = self.replace_pinyin2(sentence, pinyin_str)
                    outfile.write(f"{sentence}\t{modified_pinyin}\t{label}\n")

    def replace_pinyin2(sentence: str, pinyin_str: str) -> str:
        return
        hanzi_list = list(sentence)
        pinyin_list = pinyin_str.split()
        
        # 生成汉字的拼音，保留格式（不带声调）
        generated_pinyin = lazy_pinyin(sentence)
        generated_pinyin = [item[0] for item in generated_pinyin]
        
        # 替换俞的拼音
        for i, char in enumerate(hanzi_list):
            if char == '俞' and pinyin_list[i] == 'yu':
                pinyin_list[i] = 'shu'
        
        return ' '.join(pinyin_list)
