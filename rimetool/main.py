import os
from rimetool.utils import vcf
from rimetool.utils import singleword
from rimetool.utils import singlechinese
from rimetool.utils import tosougou
from rimetool.utils import epub

from rimetool.epub.process_epub import EpubProcessor
from rimetool.epub import epub_tools
import argparse

# import utils.singleword as singleword

def get_args_parser(add_help=True):

	parser = argparse.ArgumentParser(description='rime输入法相关工具', add_help=add_help)
	parser.add_argument('--input-path', '-i', required=True, type=str, help='需要处理的文件路径')
	parser.add_argument('--output-path', '-o',default='./rimetool_output', type=str, help='输出文件路径')
	parser.add_argument('--tool', '-t', required=True,choices=['vcf','singleword','singlechinese','tosougou','epub','hello'],type=str, help='选择工具')

	
	return parser

def main():
	parser = get_args_parser()
	args = parser.parse_args()
	
	# if not os.path.exists('./rimetool_cache'):
		# os.makedirs('./rimetool_cache')
	if not os.path.exists(args.output_path):
		os.makedirs(args.output_path)
	os.makedirs(args.output_path, exist_ok=True)
	if args.tool == 'vcf':
		vcf.main(args.input_path, args.output_path)
	elif args.tool == 'singleword':
		singleword.main(args.input_path, args.output_path)
	elif args.tool == 'singlechinese':
		singlechinese.main(args.input_path, args.output_path)
	elif args.tool == 'tosougou':
		tosougou.main(args.input_path, args.output_path)
	elif args.tool == 'epub':
		input_path= args.input_path
		output_dir = args.output_path
		output_path = args.output_path
		output_files = {
			'clean': os.path.join(args.output_path, "清理.txt"),  # 清理后的原始内容
			'short': os.path.join(args.output_path, "短句拆分.txt"),  # 短句拆分结果
			'long': os.path.join(args.output_path, "长句拆分.txt")  # 长句拆分结果
		}
		epub.main(input_path, output_dir,output_path,output_files)

	else:
		print('这里有问题')
	
	


if __name__ == "__main__":
	main()
