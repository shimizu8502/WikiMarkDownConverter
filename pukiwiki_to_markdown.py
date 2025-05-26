import argparse
import os
import re
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk # ttk をインポート
import configparser # 設定ファイルの読み書き用
import datetime # エラーログのタイムスタンプ用

CONFIG_FILE = 'converter_settings.ini'
CONFIG_SECTION = 'Paths'
KEY_PUKIWIKI_DIR = 'PukiwikiDir'
KEY_MARKDOWN_DIR = 'MarkdownDir'
KEY_ENCODING = 'Encoding'
ERROR_LOG_FILE = 'conversion_errors.log' # エラーログファイル名
LOG_DIR = 'logs' # エラーログを保存するディレクトリ

def write_error_log(message):
    """エラーメッセージをタイムスタンプ付きでログファイルに書き込みます。"""
    try:
        # ログディレクトリが存在しない場合は作成
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        
        log_file_path = os.path.join(LOG_DIR, ERROR_LOG_FILE)
        with open(log_file_path, 'a', encoding='utf-8') as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except IOError as e:
        # ログファイルへの書き込み自体に失敗した場合はコンソールに出力
        print(f"重大なエラー: ログファイル '{log_file_path}' への書き込みに失敗しました: {e}", file=sys.stderr)
        print(f"元のエラーメッセージ: {message}", file=sys.stderr)
    except Exception as e:
        print(f"ログ書き込み中に予期しないエラーが発生しました: {e}", file=sys.stderr)
        print(f"元のエラーメッセージ: {message}", file=sys.stderr)

def save_settings(pukiwiki_dir, markdown_dir, encoding):
    """選択されたディレクトリとエンコーディング設定をINIファイルに保存します。"""
    config = configparser.ConfigParser()
    config[CONFIG_SECTION] = {
        KEY_PUKIWIKI_DIR: pukiwiki_dir,
        KEY_MARKDOWN_DIR: markdown_dir,
        KEY_ENCODING: encoding
    }
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
    except IOError as e:
        print(f"設定ファイルの保存中にエラーが発生しました: {e}", file=sys.stderr)

def load_settings():
    """INIファイルからディレクトリとエンコーディング設定を読み込みます。"""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE, encoding='utf-8')
            pukiwiki_dir = config.get(CONFIG_SECTION, KEY_PUKIWIKI_DIR, fallback='')
            markdown_dir = config.get(CONFIG_SECTION, KEY_MARKDOWN_DIR, fallback='')
            encoding = config.get(CONFIG_SECTION, KEY_ENCODING, fallback='auto')
            return pukiwiki_dir, markdown_dir, encoding
        except (configparser.Error, IOError) as e:
            print(f"設定ファイルの読み込み中にエラーが発生しました: {e}", file=sys.stderr)
    return '', '', 'auto' # デフォルト値

def convert_pukiwiki_to_markdown(pukiwiki_text):
    """
    PukiWikiのテキストをMarkdown形式に変換します。
    """
    markdown_text = pukiwiki_text

    # コメントを除去 (行頭または空白の後の // から行末まで)
    # 以前の実装: markdown_text = re.sub(r'//.*$', '', markdown_text, flags=re.MULTILINE)
    # URLのhttps://などが誤って削除されるのを防ぐため、行頭または空白の後の//のみをコメントとして扱う
    markdown_text = re.sub(r'(^|\s)//.*$', r'\1', markdown_text, flags=re.MULTILINE)

    # 見出しの変換
    markdown_text = re.sub(r'^\*\*\*(.+)$', r'### \1', markdown_text, flags=re.MULTILINE)
    markdown_text = re.sub(r'^\*\*(.+)$', r'## \1', markdown_text, flags=re.MULTILINE)
    markdown_text = re.sub(r'^\*(.+)$', r'# \1', markdown_text, flags=re.MULTILINE)

    # リストの変換
    markdown_text = re.sub(r'^- (.+)$', r'- \1', markdown_text, flags=re.MULTILINE)
    markdown_text = re.sub(r'^\+ (.+)$', r'* \1', markdown_text, flags=re.MULTILINE) # PukiWikiの '+' リストは '*' に変換
    
    # ハイフンとテキストの間にスペースがない場合、スペースを追加
    markdown_text = re.sub(r'^-([^ ].+)$', r'- \1', markdown_text, flags=re.MULTILINE)  # 単一ハイフン
    markdown_text = re.sub(r'^--([^ ].+)$', r'-- \1', markdown_text, flags=re.MULTILINE)  # 二重ハイフン
    markdown_text = re.sub(r'^---([^ ].+)$', r'---- \1', markdown_text, flags=re.MULTILINE)  # 三重ハイフン→四重ハイフン

    # 強調の変換
    markdown_text = re.sub(r"'''(.*?)'''", r'**\1**', markdown_text)
    markdown_text = re.sub(r"''(.*?)''", r'*\1*', markdown_text)
    
    # 取り消し線の変換 (PukiWiki: %%text%% -> Obsidian: ~~text~~)
    # 前後のスペースを削除して変換する
    markdown_text = re.sub(r"%%(.+?)%%", lambda m: f'~~{m.group(1).strip()}~~', markdown_text)

    # リンクの変換 [[エイリアス>ページ名]] -> [[ページ名|エイリアス]] (Obsidian形式)
    markdown_text = re.sub(r'\[\[([^>\]]+)>([^\]]+)\]\]', r'[[\2|\1]]', markdown_text)
    # リンクの変換 [[ページ名]] -> [[ページ名]] (Obsidian形式, .md を削除)
    markdown_text = re.sub(r'\[\[([^\]>]+)\]\]', r'[[\1]]', markdown_text)

    # 画像の変換 #ref(画像URL,altテキスト) -> ![altテキスト](画像URL)
    markdown_text = re.sub(r'#ref\(([^,]+),?([^)]*)\)', r'![\2](\1)', markdown_text)

    # 行頭のbr/BRを改行に変換
    markdown_text = re.sub(r'^#br\s*$', '\n', markdown_text, flags=re.MULTILINE)
    markdown_text = re.sub(r'^#BR\s*$', '\n', markdown_text, flags=re.MULTILINE)

    # 整形済みテキスト (行頭が半角スペース) の変換
    # 元のテキスト位置を保持しながら処理
    lines = markdown_text.split('\n')
    processed_lines = []
    in_preformatted_block = False
    current_block = []

    for line in lines:
        if line.startswith(' '):
            if not in_preformatted_block:
                in_preformatted_block = True
                current_block = []
            current_block.append(line[1:])  # 先頭のスペースを除去
        else:
            if in_preformatted_block:
                # 整形済みテキストブロックの終了 - その場でコードブロックに変換
                code_block = "```\n" + "\n".join(current_block) + "\n```"
                processed_lines.append(code_block)
                current_block = []
                in_preformatted_block = False
            processed_lines.append(line)

    # ファイル末尾が整形済みテキストの場合
    if in_preformatted_block:
        code_block = "```\n" + "\n".join(current_block) + "\n```"
        processed_lines.append(code_block)

    # processed_lines を結合してテキストを再構築
    markdown_text = "\n".join(processed_lines)

    # カンマ区切りテーブルの変換
    # 例: ,A,B,C や 空欄,A,B,C
    csv_table_lines = []
    csv_other_lines = []
    is_csv_table = False
    for line in markdown_text.split('\n'):
        # 行頭がカンマで始まるか、カンマを含む行を検出
        if line.startswith(',') or (re.match(r'^[^,]+,', line) and line.count(',') >= 2):
            # すでにテーブル行として処理されていないか確認（|| や | で始まる行は除外）
            if not line.startswith('|'):
                csv_table_lines.append(line)
                is_csv_table = True
                continue
        
        # テーブル行でない場合、または区切りを検出した場合
        if is_csv_table and csv_table_lines and (not line.startswith(',') and not re.match(r'^[^,]+,', line)):
            # テーブルの終了を検出
            header = csv_table_lines[0]
            header_cells = header.split(',')
            
            # 先頭のセルが空の場合は除外
            if header_cells[0] == '':
                header_cells = header_cells[1:]
            
            # テーブルのヘッダー行を生成
            markdown_table = "| " + " | ".join(header_cells) + " |\n"
            # 区切り行を生成
            markdown_table += "| " + " | ".join(["---"] * len(header_cells)) + " |\n"
            
            # データ行の処理
            for row_line in csv_table_lines[1:]:
                cells = row_line.split(',')
                
                # 先頭のセルが空の場合は除外
                if cells[0] == '':
                    cells = cells[1:]
                
                # セル数がヘッダーセル数より少ない場合、空セルで埋める
                while len(cells) < len(header_cells):
                    cells.append('')
                
                # ヘッダーセル数より多い場合は切り捨て
                cells = cells[:len(header_cells)]
                
                markdown_table += "| " + " | ".join(cells) + " |\n"
            
            csv_other_lines.append("") # テーブルの前に改行を挿入
            csv_other_lines.append(markdown_table)
            
            # テーブル処理の終了
            csv_table_lines = []
            is_csv_table = False
        
        if not is_csv_table:
            csv_other_lines.append(line)
    
    # ファイル末尾がカンマ区切りテーブルの場合の処理
    if is_csv_table and csv_table_lines:
        header = csv_table_lines[0]
        header_cells = header.split(',')
        
        # 先頭のセルが空の場合は除外
        if header_cells[0] == '':
            header_cells = header_cells[1:]
        
        # テーブルのヘッダー行を生成
        markdown_table = "| " + " | ".join(header_cells) + " |\n"
        # 区切り行を生成
        markdown_table += "| " + " | ".join(["---"] * len(header_cells)) + " |\n"
        
        # データ行の処理
        for row_line in csv_table_lines[1:]:
            cells = row_line.split(',')
            
            # 先頭のセルが空の場合は除外
            if cells[0] == '':
                cells = cells[1:]
            
            # セル数がヘッダーセル数より少ない場合、空セルで埋める
            while len(cells) < len(header_cells):
                cells.append('')
            
            # ヘッダーセル数より多い場合は切り捨て
            cells = cells[:len(header_cells)]
            
            markdown_table += "| " + " | ".join(cells) + " |\n"
        
        csv_other_lines.append("") # テーブルの前に改行を挿入
        csv_other_lines.append(markdown_table)
    
    markdown_text = "\n".join(csv_other_lines)

    # 表組みの変換 (簡易的な対応)
    # |A|B|C| や |~A|~B|~C| や |A|B|C|h (ヘッダー行)
    table_lines = []
    other_lines = []
    is_table = False
    for line in markdown_text.split('\n'):
        # |h で終わる行（ヘッダー行）や |で終わる行をテーブル行として認識
        if line.startswith('|') and (line.endswith('|') or line.endswith('|h')):
            # |h で終わる行は |h を除去してからテーブル行として追加
            if line.endswith('|h'):
                line = line[:-1]  # |h の h を除去して | で終わるようにする
            table_lines.append(line)
            is_table = True
        else:
            if is_table: # 表の終わり
                if table_lines:
                    header = table_lines[0]
                    header_cells = [cell.strip('~') for cell in header.strip('|').split('|')]
                    
                    # CENTER:, C: などの揃え指定をヘッダーセルから除去
                    cleaned_header_cells = []
                    for cell in header_cells:
                        cell = cell.strip()
                        if cell.startswith(('CENTER:', 'C:')):
                            cell = cell[7:].strip()
                        elif cell.startswith(('RIGHT:', 'R:')):
                            cell = cell[6:].strip()
                        elif cell.startswith(('LEFT:', 'L:')):
                            cell = cell[5:].strip()
                        cleaned_header_cells.append(cell)
                    
                    markdown_table = "| " + " | ".join(cleaned_header_cells) + " |\n"
                    
                    # 各列の配置を分析
                    column_alignments = []
                    for col_idx in range(len(cleaned_header_cells)):
                        col_alignment = "---"  # デフォルトは左揃え
                        
                        # ヘッダー行から配置情報を取得
                        if col_idx < len(header_cells):
                            original_cell = header_cells[col_idx].strip()
                            if original_cell.startswith(('CENTER:', 'C:')):
                                col_alignment = ":---:"
                            elif original_cell.startswith(('RIGHT:', 'R:')):
                                col_alignment = "---:"
                            elif original_cell.startswith(('LEFT:', 'L:')):
                                col_alignment = ":---"
                        
                        # データ行からも配置情報を確認（ヘッダーで指定されていない場合）
                        if col_alignment == "---":
                            for row_idx in range(1, len(table_lines)):
                                cells = table_lines[row_idx].strip('|').split('|')
                                if col_idx < len(cells):
                                    cell_content = cells[col_idx].strip()
                                    # CENTER:, C: 指定の確認（中央揃え）
                                    if cell_content.startswith(('CENTER:', 'C:')):
                                        col_alignment = ":---:"
                                        break
                                    # RIGHT:, R: 指定の確認（右揃え）
                                    elif cell_content.startswith(('RIGHT:', 'R:')):
                                        col_alignment = "---:"
                                        break
                                    # LEFT:, L: 指定の確認（左揃え - 明示的に指定された場合）
                                    elif cell_content.startswith(('LEFT:', 'L:')):
                                        col_alignment = ":---"
                                        break
                        
                        column_alignments.append(col_alignment)
                    
                    # 区切り行の作成
                    markdown_table += "| " + " | ".join(column_alignments) + " |\n"
                    
                    # データ行の処理
                    for row_line in table_lines[1:]:
                        row_cells = []
                        cells = row_line.strip('|').split('|')
                        
                        for i, cell in enumerate(cells):
                            cell = cell.strip('~').strip()
                            # 揃え指定を削除
                            if cell.startswith(('CENTER:', 'C:')):
                                if cell.startswith('CENTER:'):
                                    cell = cell[7:].strip()
                                else:  # C:
                                    cell = cell[2:].strip()
                            elif cell.startswith(('RIGHT:', 'R:')):
                                if cell.startswith('RIGHT:'):
                                    cell = cell[6:].strip()
                                else:  # R:
                                    cell = cell[2:].strip()
                            elif cell.startswith(('LEFT:', 'L:')):
                                if cell.startswith('LEFT:'):
                                    cell = cell[5:].strip()
                                else:  # L:
                                    cell = cell[2:].strip()
                            
                            row_cells.append(cell)
                        
                        markdown_table += "| " + " | ".join(row_cells) + " |\n"
                    
                    other_lines.append("") # テーブルの前に改行を挿入
                    other_lines.append(markdown_table)
                table_lines = []
                is_table = False
            other_lines.append(line)

    if is_table and table_lines: # ファイル末尾が表の場合
        header = table_lines[0]
        header_cells = [cell.strip('~') for cell in header.strip('|').split('|')]
        
        # CENTER:, C: などの揃え指定をヘッダーセルから除去
        cleaned_header_cells = []
        for cell in header_cells:
            cell = cell.strip()
            if cell.startswith(('CENTER:', 'C:')):
                if cell.startswith('CENTER:'):
                    cell = cell[7:].strip()
                else:  # C:
                    cell = cell[2:].strip()
            elif cell.startswith(('RIGHT:', 'R:')):
                if cell.startswith('RIGHT:'):
                    cell = cell[6:].strip()
                else:  # R:
                    cell = cell[2:].strip()
            elif cell.startswith(('LEFT:', 'L:')):
                if cell.startswith('LEFT:'):
                    cell = cell[5:].strip()
                else:  # L:
                    cell = cell[2:].strip()
            cleaned_header_cells.append(cell)
        
        markdown_table = "| " + " | ".join(cleaned_header_cells) + " |\n"
        
        # 各列の配置を分析
        column_alignments = []
        for col_idx in range(len(cleaned_header_cells)):
            col_alignment = "---"  # デフォルトは左揃え
            
            # ヘッダー行から配置情報を取得
            if col_idx < len(header_cells):
                original_cell = header_cells[col_idx].strip()
                if original_cell.startswith(('CENTER:', 'C:')):
                    col_alignment = ":---:"
                elif original_cell.startswith(('RIGHT:', 'R:')):
                    col_alignment = "---:"
                elif original_cell.startswith(('LEFT:', 'L:')):
                    col_alignment = ":---"
            
            # データ行からも配置情報を確認（ヘッダーで指定されていない場合）
            if col_alignment == "---":
                for row_idx in range(1, len(table_lines)):
                    cells = table_lines[row_idx].strip('|').split('|')
                    if col_idx < len(cells):
                        cell_content = cells[col_idx].strip()
                        # CENTER:, C: 指定の確認（中央揃え）
                        if cell_content.startswith(('CENTER:', 'C:')):
                            col_alignment = ":---:"
                            break
                        # RIGHT:, R: 指定の確認（右揃え）
                        elif cell_content.startswith(('RIGHT:', 'R:')):
                            col_alignment = "---:"
                            break
                        # LEFT:, L: 指定の確認（左揃え - 明示的に指定された場合）
                        elif cell_content.startswith(('LEFT:', 'L:')):
                            col_alignment = ":---"
                            break
            
            column_alignments.append(col_alignment)
        
        # 区切り行の作成
        markdown_table += "| " + " | ".join(column_alignments) + " |\n"
        
        # データ行の処理
        for row_line in table_lines[1:]:
            row_cells = []
            cells = row_line.strip('|').split('|')
            
            for i, cell in enumerate(cells):
                cell = cell.strip('~').strip()
                # 揃え指定を削除
                if cell.startswith(('CENTER:', 'C:')):
                    if cell.startswith('CENTER:'):
                        cell = cell[7:].strip()
                    else:  # C:
                        cell = cell[2:].strip()
                elif cell.startswith(('RIGHT:', 'R:')):
                    if cell.startswith('RIGHT:'):
                        cell = cell[6:].strip()
                    else:  # R:
                        cell = cell[2:].strip()
                elif cell.startswith(('LEFT:', 'L:')):
                    if cell.startswith('LEFT:'):
                        cell = cell[5:].strip()
                    else:  # L:
                        cell = cell[2:].strip()
                
                row_cells.append(cell)
            
            markdown_table += "| " + " | ".join(row_cells) + " |\n"
        
        other_lines.append("") # テーブルの前に改行を挿入
        other_lines.append(markdown_table)

    markdown_text = "\n".join(other_lines)

    return markdown_text.strip()

def detect_encoding(file_path):
    """
    ファイルの文字コードを判定します。
    判定可能な文字コード: UTF-8, EUC-JP, Shift_JIS
    """
    encodings_to_try = ['utf-8', 'euc-jp', 'shift_jis']
    for enc in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read()
            return enc
        except UnicodeDecodeError:
            continue
    return None # 判定できなかった場合

def process_conversion(pukiwiki_dir, markdown_dir, specified_encoding=None, progress_bar=None, status_var=None, root_window=None):
    """
    PukiWikiからMarkdownへの変換処理を実行します。
    main()関数からロジックを分離。
    GUIの進捗表示ウィジェットを更新する機能を追加。
    """
    if not pukiwiki_dir or not markdown_dir:
        messagebox.showerror("エラー", "PukiWikiディレクトリとMarkdown出力ディレクトリの両方を選択してください。")
        return

    if not os.path.isdir(pukiwiki_dir):
        messagebox.showerror("エラー", f"PukiWikiディレクトリ '{pukiwiki_dir}' が見つかりません。")
        return

    if not os.path.exists(markdown_dir):
        try:
            os.makedirs(markdown_dir)
            print(f"出力ディレクトリ '{markdown_dir}' を作成しました。")
        except OSError as e:
            messagebox.showerror("エラー", f"出力ディレクトリ '{markdown_dir}' の作成に失敗しました: {e}")
            return
    elif not os.path.isdir(markdown_dir):
        messagebox.showerror("エラー", f"出力先 '{markdown_dir}' はディレクトリではありません。")
        return

    # --- 出力ディレクトリ内の既存 .md ファイルを削除 --- START
    if os.path.exists(markdown_dir) and os.path.isdir(markdown_dir):
        confirm_delete = messagebox.askyesno(
            "確認",
            f"出力ディレクトリ '{markdown_dir}' 内の既存の .md ファイルをすべて削除しますか？\n"
            f"この操作は元に戻せません。"
        )
        if confirm_delete:
            deleted_count = 0
            errors_deleting = False
            try:
                for item in os.listdir(markdown_dir):
                    if item.endswith('.md'):
                        item_path = os.path.join(markdown_dir, item)
                        try:
                            os.remove(item_path)
                            print(f"  削除しました: {item_path}")
                            deleted_count += 1
                        except OSError as e_remove:
                            error_message = f"エラー: ファイル '{item_path}' の削除に失敗しました: {e_remove}"
                            print(error_message, file=sys.stderr)
                            write_error_log(error_message)
                            errors_deleting = True
                if deleted_count > 0:
                    messagebox.showinfo("情報", f"{deleted_count}個の .md ファイルを削除しました。")
                elif not errors_deleting:
                    messagebox.showinfo("情報", "出力ディレクトリに削除対象の .md ファイルはありませんでした。")
                if errors_deleting:
                    messagebox.showwarning("警告", "一部の .md ファイルの削除中にエラーが発生しました。詳細はコンソールを確認してください。")
            except Exception as e_list:
                error_message = f"出力ディレクトリのファイル一覧取得中にエラー: {e_list}"
                print(f"エラー: {error_message}", file=sys.stderr)
                write_error_log(error_message)
                messagebox.showerror("エラー", error_message)
                return # ディレクトリ操作エラー時は処理中断
        else:
            messagebox.showinfo("情報", "既存の .md ファイルの削除はキャンセルされました。変換処理を続行します。")
    # --- 出力ディレクトリ内の既存 .md ファイルを削除 --- END

    print(f"処理開始: PukiWikiディレクトリ '{pukiwiki_dir}' -> Markdownディレクトリ '{markdown_dir}'")
    file_count = 0
    error_count = 0
    # プログレス表示用のテキストエリアなどをGUIに追加することも検討できる

    # 処理対象ファイルリストの取得
    files_to_process = []
    for filename in os.listdir(pukiwiki_dir):
        pukiwiki_filepath = os.path.join(pukiwiki_dir, filename)
        if os.path.isfile(pukiwiki_filepath) and (filename.endswith('.txt') or filename.endswith('.page')):
            files_to_process.append(filename)
    
    total_files = len(files_to_process)
    if progress_bar:
        progress_bar["maximum"] = total_files
        progress_bar["value"] = 0
    
    processed_count = 0

    for filename in files_to_process: # os.listdir(pukiwiki_dir)から変更
        pukiwiki_filepath = os.path.join(pukiwiki_dir, filename)
        # if os.path.isfile(pukiwiki_filepath) and (filename.endswith('.txt') or filename.endswith('.page')): # このチェックは上で実施済み
        original_basename, ext = os.path.splitext(filename)
        decoded_basename = original_basename
        try:
            # ファイル名がすべて16進数文字で構成され、かつ偶数長であるかを確認
            # あまりにも短いファイル名は誤変換の可能性を考慮し、一定長以上(例: 4文字以上)を対象とする
            if all(c in '0123456789abcdefABCDEF' for c in original_basename) and len(original_basename) % 2 == 0 and len(original_basename) >= 2:
                decoded_bytes = bytes.fromhex(original_basename)
                decoded_basename_candidate = decoded_bytes.decode('utf-8')
                # デコード結果が空文字列や制御文字のみになる場合などを避けるため、
                # 簡単なチェックとして、デコード後も何らかの表示可能文字が含まれることを期待する。
                # より厳密には、デコード後の文字列が妥当なファイル名文字だけで構成されているかを確認すべきだが、
                # ここではPukiWikiのエンコード仕様が不明なため、一旦デコード成功をもって良しとする。
                # ただし、元のファイル名と全く同じ場合はヘキサエンコードではなかったとみなす。
                if decoded_basename_candidate != original_basename:
                    decoded_basename = decoded_basename_candidate
                    print(f"  情報: ファイル名 '{original_basename}{ext}' を '{decoded_basename}{ext}' にデコードしました。")
        except ValueError:
            # fromhexでエラー (奇数長や16進数以外の文字が含まれる場合など)
            # この場合はヘキサエンコードされたファイル名ではないと判断し、元のファイル名を使用
            pass
        except UnicodeDecodeError:
            error_message = f"  警告: ファイル名 '{original_basename}{ext}' のUTF-8デコードに失敗しました。元のファイル名を使用します。"
            print(error_message, file=sys.stderr)
            write_error_log(error_message)

        # Windowsの不正ファイル名文字を安全な文字に置換
        # 不正な文字: < > : " | ? * および制御文字
        # また、ファイル名に / が含まれる場合はディレクトリ区切り文字として認識されるため、全角スラッシュに置換
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            decoded_basename = decoded_basename.replace(char, '_')
        
        # スラッシュとバックスラッシュも安全な文字に置換
        decoded_basename = decoded_basename.replace('/', '／')  # 全角スラッシュ
        decoded_basename = decoded_basename.replace('\\', '￥')  # 全角円記号
        
        # 制御文字の除去
        decoded_basename = ''.join(char for char in decoded_basename if ord(char) >= 32)
        
        # ファイル名が空になった場合のフォールバック
        if not decoded_basename.strip():
            decoded_basename = original_basename

        markdown_filename = decoded_basename + '.md'
        markdown_filepath = os.path.join(markdown_dir, markdown_filename)

        try:
            encoding_to_use = specified_encoding
            if not encoding_to_use:
                encoding_to_use = detect_encoding(pukiwiki_filepath)

            if not encoding_to_use:
                error_message = f"警告: ファイル '{pukiwiki_filepath}' の文字コードを自動判別できませんでした。UTF-8として処理を試みます。"
                print(error_message, file=sys.stderr)
                write_error_log(error_message)
                encoding_to_use = 'utf-8' # デフォルトフォールバック

            with open(pukiwiki_filepath, 'r', encoding=encoding_to_use, errors='replace') as f:
                pukiwiki_content = f.read()

            print(f"  変換中: '{pukiwiki_filepath}' (encoding: {encoding_to_use})")
            markdown_content = convert_pukiwiki_to_markdown(pukiwiki_content)

            with open(markdown_filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            file_count += 1
        except Exception as e:
            error_message = f"エラー: ファイル '{pukiwiki_filepath}' の変換中にエラーが発生しました: {e}"
            print(error_message, file=sys.stderr)
            write_error_log(error_message)
            error_count += 1
        finally:
            processed_count += 1
            if progress_bar:
                progress_bar["value"] = processed_count
                # プログレス情報更新関数が存在する場合は呼び出し
                if hasattr(progress_bar, 'update_progress_info'):
                    progress_bar.update_progress_info(processed_count, total_files)
            if status_var:
                status_var.set(f"🔄 処理中: {filename} ({processed_count}/{total_files})")
            if root_window:
                root_window.update_idletasks()

    if status_var:
        if error_count > 0:
            status_var.set(f"⚠️ 処理完了: {file_count}/{total_files} ファイルを変換しました（{error_count} 件のエラー）")
        else:
            status_var.set(f"✅ 処理完了: {file_count}/{total_files} ファイルを変換しました")

    result_message = f"処理完了: {file_count} 個のファイルを変換しました。"
    if error_count > 0:
        result_message += f"\n注意: {error_count} 個のファイルでエラーが発生しました。"
        result_message += f"\nエラーの詳細は '{os.path.join(LOG_DIR, ERROR_LOG_FILE)}' を確認してください。"
    print(result_message)
    messagebox.showinfo("処理完了", result_message)

    # --- 変換されたMarkdownファイルを1つに連結してlogsディレクトリに保存 --- START
    try:
        if file_count > 0: # 変換されたファイルが1つ以上ある場合のみ実行
            if not os.path.exists(LOG_DIR):
                os.makedirs(LOG_DIR)
            
            today_str = datetime.datetime.now().strftime("%Y_%m_%d")
            concatenated_filename = f"{today_str}_obsidian.md"
            concatenated_filepath = os.path.join(LOG_DIR, concatenated_filename)
            
            all_markdown_content = []
            # markdown_dir 内の .md ファイルをソートして取得 (順序をある程度一定にするため)
            md_files = sorted([f for f in os.listdir(markdown_dir) if f.endswith('.md')])

            for md_filename in md_files:
                md_filepath = os.path.join(markdown_dir, md_filename)
                try:
                    with open(md_filepath, 'r', encoding='utf-8') as f_md:
                        content = f_md.read()
                    all_markdown_content.append(f"\n\n---\n## FILE: {md_filename}\n---\n\n{content}")
                except Exception as e_read_md:
                    error_message = f"連結用Markdownファイル '{md_filepath}' の読み込み中にエラー: {e_read_md}"
                    print(error_message, file=sys.stderr)
                    write_error_log(error_message)
            
            if all_markdown_content:
                with open(concatenated_filepath, 'w', encoding='utf-8') as f_concat:
                    f_concat.write("".join(all_markdown_content))
                print(f"情報: 変換されたMarkdownファイルを連結し、'{concatenated_filepath}' に保存しました。")
                messagebox.showinfo("追加処理完了", f"変換されたMarkdownファイルを連結し、\n'{concatenated_filepath}'\nに保存しました。")
            else:
                print("情報: 連結対象のMarkdownファイルが見つからなかったため、連結ファイルの作成はスキップされました。")

    except Exception as e_concat:
        error_message = f"Markdownファイルの連結処理中にエラーが発生しました: {e_concat}"
        print(error_message, file=sys.stderr)
        write_error_log(error_message)
        messagebox.showerror("連結エラー", error_message)
    # --- 変換されたMarkdownファイルを1つに連結してlogsディレクトリに保存 --- END


def main_gui():
    """
    GUIアプリケーションのメイン処理
    """
    window = tk.Tk()
    window.title("PukiWiki to Markdown Converter v1.2")
    window.geometry("700x500")
    window.minsize(600, 450)
    
    # ウィンドウを画面中央に配置
    window.eval('tk::PlaceWindow . center')
    
    # アイコン設定（オプション）
    try:
        # window.iconbitmap('icon.ico')  # アイコンファイルがある場合
        pass
    except:
        pass

    # --- カラーパレットの定義 ---
    colors = {
        'bg_primary': '#f8f9fa',
        'bg_secondary': '#ffffff', 
        'bg_accent': '#007bff',
        'text_primary': '#212529',
        'text_secondary': '#6c757d',
        'border': '#dee2e6',
        'success': '#28a745',
        'warning': '#ffc107'
    }
    
    # メインウィンドウの背景色設定
    window.configure(bg=colors['bg_primary'])

    # --- フォント設定 ---
    import tkinter.font as tkfont
    try:
        font_title = tkfont.Font(family="Yu Gothic UI", size=14, weight="bold")
        font_label = tkfont.Font(family="Yu Gothic UI", size=10)
        font_button = tkfont.Font(family="Yu Gothic UI", size=10, weight="bold")
        font_status = tkfont.Font(family="Yu Gothic UI", size=9)
    except:
        # フォントが利用できない場合のフォールバック
        font_title = tkfont.Font(size=14, weight="bold")
        font_label = tkfont.Font(size=10)
        font_button = tkfont.Font(size=10, weight="bold")
        font_status = tkfont.Font(size=9)

    # --- スタイルの設定 ---
    style = ttk.Style()
    
    # 利用可能なテーマを確認して設定
    if 'vista' in style.theme_names():
        style.theme_use('vista')
    elif 'clam' in style.theme_names():
        style.theme_use('clam')
    
    # カスタムスタイルの設定
    style.configure('Title.TLabel', font=font_title, foreground=colors['text_primary'])
    style.configure('Heading.TLabel', font=font_label, foreground=colors['text_primary'], background=colors['bg_primary'])
    style.configure('Custom.TButton', font=font_button, padding=(10, 8))
    style.configure('Action.TButton', font=font_button, padding=(15, 10))
    style.configure('Status.TLabel', font=font_status, foreground=colors['text_secondary'], background=colors['bg_primary'])
    
    # プログレスバーのスタイル
    style.configure('Custom.Horizontal.TProgressbar', 
                   troughcolor=colors['border'], 
                   borderwidth=1, 
                   lightcolor=colors['success'], 
                   darkcolor=colors['success'],
                   thickness=20)

    # --- 設定の読み込み ---
    initial_pukiwiki_dir, initial_markdown_dir, initial_encoding = load_settings()
    pukiwiki_dir_var = tk.StringVar(value=initial_pukiwiki_dir)
    markdown_dir_var = tk.StringVar(value=initial_markdown_dir)
    encoding_var = tk.StringVar(value=initial_encoding)

    def select_pukiwiki_dir():
        dir_path = filedialog.askdirectory(title="PukiWikiデータディレクトリを選択")
        if dir_path:
            pukiwiki_dir_var.set(dir_path)

    def select_markdown_dir():
        dir_path = filedialog.askdirectory(title="Markdown出力ディレクトリを選択") 
        if dir_path:
            markdown_dir_var.set(dir_path)

    def start_conversion():
        p_dir = pukiwiki_dir_var.get()
        m_dir = markdown_dir_var.get()
        enc = encoding_var.get()
        
        # エンコーディング値の正規化
        if enc == "auto (自動判別)":
            enc = "auto"
        
        save_settings(p_dir, m_dir, enc)
        specified_enc = enc if enc != "auto" else None
        process_conversion(p_dir, m_dir, specified_enc, progress_bar, status_var, window)

    # --- メインコンテナフレーム ---
    main_frame = ttk.Frame(window, padding="20 20 20 10")
    main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    # ウィンドウのサイズ変更に対応
    window.grid_rowconfigure(0, weight=1)
    window.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(6, weight=1)  # プログレスエリアの行を拡張可能に
    main_frame.grid_columnconfigure(1, weight=1)

    # --- タイトル ---
    title_label = ttk.Label(main_frame, text="📝 PukiWiki to Markdown Converter", style='Title.TLabel')
    title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="ew")

    # --- 入力ディレクトリ選択セクション ---
    input_frame = ttk.LabelFrame(main_frame, text=" 📁 入力設定 ", padding="15 10 15 15")
    input_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 15))
    input_frame.grid_columnconfigure(1, weight=1)

    # PukiWikiディレクトリ選択
    ttk.Label(input_frame, text="PukiWikiデータディレクトリ:", style='Heading.TLabel').grid(row=0, column=0, padx=(0, 10), pady=(0, 8), sticky="w")
    pukiwiki_entry = ttk.Entry(input_frame, textvariable=pukiwiki_dir_var, font=font_label)
    pukiwiki_entry.grid(row=0, column=1, padx=(0, 10), pady=(0, 8), sticky="ew")
    ttk.Button(input_frame, text="📂 選択", command=select_pukiwiki_dir, style='Custom.TButton').grid(row=0, column=2, pady=(0, 8))

    # Markdown出力ディレクトリ選択  
    ttk.Label(input_frame, text="Markdown出力ディレクトリ:", style='Heading.TLabel').grid(row=1, column=0, padx=(0, 10), pady=(0, 8), sticky="w")
    markdown_entry = ttk.Entry(input_frame, textvariable=markdown_dir_var, font=font_label)
    markdown_entry.grid(row=1, column=1, padx=(0, 10), pady=(0, 8), sticky="ew")
    ttk.Button(input_frame, text="📂 選択", command=select_markdown_dir, style='Custom.TButton').grid(row=1, column=2, pady=(0, 8))

    # 文字コード指定
    ttk.Label(input_frame, text="入力文字コード:", style='Heading.TLabel').grid(row=2, column=0, padx=(0, 10), sticky="w")
    encoding_options = ["auto (自動判別)", "utf-8", "euc-jp", "shift_jis"]
    encoding_combo = ttk.Combobox(input_frame, textvariable=encoding_var, values=encoding_options, state="readonly", font=font_label, width=20)
    encoding_combo.grid(row=2, column=1, padx=(0, 10), sticky="w")
    
    # エンコーディング設定の初期化
    if initial_encoding == "auto":
        encoding_combo.set("auto (自動判別)")
        encoding_var.set("auto")  # 内部変数は"auto"に設定
    else:
        if initial_encoding in ["utf-8", "euc-jp", "shift_jis"]:
            encoding_combo.set(initial_encoding)
            encoding_var.set(initial_encoding)
        else:
            encoding_combo.set("auto (自動判別)")
            encoding_var.set("auto")
    
    # エンコーディング変数の更新処理
    def update_encoding(*args):
        selected = encoding_combo.get()
        if selected == "auto (自動判別)":
            encoding_var.set("auto")
        else:
            encoding_var.set(selected)
    
    encoding_combo.bind('<<ComboboxSelected>>', update_encoding)

    # --- 実行ボタンセクション ---
    action_frame = ttk.Frame(main_frame, padding="0 15 0 15")
    action_frame.grid(row=2, column=0, columnspan=3, pady=(10, 20))
    
    convert_button = ttk.Button(action_frame, text="🚀 変換実行", command=start_conversion, style='Action.TButton')
    convert_button.pack()

    # --- プログレスセクション ---
    progress_frame = ttk.LabelFrame(main_frame, text=" 📊 処理状況 ", padding="15 10 15 15")
    progress_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 10))
    progress_frame.grid_columnconfigure(0, weight=1)

    # ステータス表示
    status_var = tk.StringVar()
    status_label = ttk.Label(progress_frame, textvariable=status_var, style='Status.TLabel', wraplength=600)
    status_label.grid(row=0, column=0, pady=(0, 10), sticky="ew")
    status_var.set("🟢 準備完了 - ディレクトリを選択して変換を開始してください")

    # プログレスバー
    progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate", style='Custom.Horizontal.TProgressbar')
    progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 5))
    
    # プログレス情報ラベル
    progress_info_var = tk.StringVar()
    progress_info_label = ttk.Label(progress_frame, textvariable=progress_info_var, style='Status.TLabel')
    progress_info_label.grid(row=2, column=0, sticky="ew")
    progress_info_var.set("")

    # --- フッター情報 ---
    footer_frame = ttk.Frame(main_frame, padding="0 10 0 0")
    footer_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(15, 0))
    
    info_text = "💡 ヒント: 変換されたファイルはObsidian互換のMarkdown形式で出力されます"
    ttk.Label(footer_frame, text=info_text, style='Status.TLabel').pack()

    # --- ウィンドウクローズ時の設定保存 ---
    def on_closing():
        p_dir = pukiwiki_dir_var.get()
        m_dir = markdown_dir_var.get()
        enc = encoding_var.get()
        
        # エンコーディング値の正規化
        if enc == "auto (自動判別)":
            enc = "auto"
            
        save_settings(p_dir, m_dir, enc)
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_closing)

    # プログレス情報更新関数をグローバルに設定
    def update_progress_info(current, total):
        if total > 0:
            percentage = int((current / total) * 100)
            progress_info_var.set(f"進捗: {current}/{total} ファイル ({percentage}%)")
        else:
            progress_info_var.set("")
    
    # プログレス情報更新関数を progress_bar に関連付け
    progress_bar.update_progress_info = update_progress_info

    window.mainloop()


if __name__ == '__main__':
    # main() # 古いコマンドラインベースのmain関数は呼び出さない
    main_gui() 