import httpx
from typing import List, Tuple, Dict
from bs4 import BeautifulSoup, element, ResultSet
from pathlib import Path

def remove_attr(statement: element.Tag):
  for td in statement.children:
    if not isinstance(td, element.Tag):
      continue
    del td['class']
    del td['style']
    
def is_data(statement: element.Tag) -> bool:
  children_count = len(list(statement.children))
  avaiable_data_count = 0
  for td in statement.children:
    if not is_data_included(td):
      continue
    avaiable_data_count += 1
  return children_count == 15 and avaiable_data_count == 7

def isfloat(txt: str) -> bool:
  try:
    # print(txt, txt.isnumeric())
    float(txt)
    return True
  except ValueError:
    return False

def is_data_included(elem: element.PageElement) -> bool:
  return (isinstance(elem, element.Tag) and 
          elem.name == 'td' and 
          len(elem.get_text().strip()) > 0)

def to_raw(statement: element.Tag) -> Tuple[str, List]:
  title = None
  data = []
  raw = []
  for td in statement.children:
    if not is_data_included(td):
      continue
    if title is None:
      title = td.get_text().strip()
      continue
    number = td.get_text().strip().replace(',', '')
    if isfloat(number):
      raw.append(float(number))
    if len(raw) == 2:
      data.append(raw)
      raw = []
  return (title, data)

def is_category(statement: element.Tag) -> bool:
  children_count = len(list(statement.children))
  empty_count = 7
  for td in statement.children:
    if (not is_data_included(td)):
      continue
    empty_count -= 1
  return children_count == 15 and empty_count == 6

def extract_statement(statements: ResultSet) -> Dict:
  results = {}
  for statement in statements:
    if is_category(statement):
      pass
    elif is_data(statement):
      remove_attr(statement)
      title, data = to_raw(statement)
      results[title] = data
  return results

def fetch_bank_financial_statement(bank_code: int, artifacts_dir: Path):
  financial_statement = open_statement(bank_code, artifacts_dir)
  if financial_statement is None:
    bs = crawl_statement(bank_code)
    financial_statement = bs.find('table', class_='hasBorder', recursive=True)
    store_financial_statenment(bank_code, financial_statement.prettify(), artifacts_dir)
    
  statements = financial_statement.find_all('tr')
  statements = extract_statement(statements)

def store_financial_statenment(bank_code: int, content: str, artifacts_dir: Path):
  statement_file = artifacts_dir.joinpath(f'{bank_code}.html')
  with open(statement_file, 'w') as f:
    f.write(content)

def open_statement(bank_code: int, artifacts_dir: Path) -> BeautifulSoup:
  statement_file = artifacts_dir.joinpath(f'{bank_code}.html')
  if not statement_file.exists():
    return None
  with open(statement_file, 'r') as fp:
    return BeautifulSoup(fp, 'html.parser')

def crawl_statement(bank_code: int) -> BeautifulSoup:
  body = {
    'encodeURIComponent': 1,
    'TYPEK': 'sii',
    'step': 2,
    'year': 111,
    'season':3,
    'co_id': bank_code,
    'firstin':1
  }
  r = httpx.post('https://mops.twse.com.tw/mops/web/ajax_t164sb03', data=body)
  return BeautifulSoup(r.content, 'html.parser')

def main():
  artifacts_dir = Path('./finance-statements/')
  artifacts_dir.mkdir(mode=0o775, exist_ok=True)
  if artifacts_dir.exists() and artifacts_dir.is_dir():
    print(f'Artifacts directory: {artifacts_dir} is existing')
    
  government_banks_code = [2880, 5880, 2892, 2801, 2886, 2834]
  for bank_code in government_banks_code:
    fetch_bank_financial_statement(bank_code, artifacts_dir)

if __name__ == '__main__':
  main()
  