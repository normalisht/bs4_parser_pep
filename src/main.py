import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, MAIN_DOC_URL, PEPS_URL, EXPECTED_STATUS
from exceptions import ParserFindTagException
from outputs import control_output
from utils import get_response, find_tag

logger = configure_logging()


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag.get('href')
        version_link = urljoin(whats_new_url, href)

        response = get_response(session, version_link)
        if response is None:
            continue

        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')

        results.append((version_link, h1.text, dl_text))

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})

    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise ParserFindTagException()

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag.get('href')

        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    doc_table = find_tag(soup, 'table', attrs={'class': 'docutils'})

    link_pattern = r'.*pdf-a4\.zip'
    pdf_a4_tag = find_tag(doc_table, 'a', {'href': re.compile(link_pattern)})
    archive_url = urljoin(downloads_url, pdf_a4_tag.get('href'))
    filename = archive_url.split('/')[-1]

    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logger.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    response = get_response(session, PEPS_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    section = find_tag(soup, 'section', {'id': 'numerical-index'})
    pep_table = find_tag(section, 'table', {'class': 'pep-zero-table'})
    peps = pep_table.tbody.find_all('tr')

    pep_statuses = {}
    mismatched_statuses = []
    for pep in tqdm(peps):
        expected_status = get_expected_status(find_tag(pep, 'abbr').text)
        pep_link = urljoin(PEPS_URL, find_tag(pep, 'a').get('href'))

        response = get_response(session, pep_link)
        if response is None:
            continue

        soup = BeautifulSoup(response.text, features='lxml')
        info_table = find_tag(soup, 'dl', {'class': 'field-list'})
        pep_status = find_tag(info_table, 'abbr').text

        if pep_status not in expected_status:
            mismatched_statuses.append(
                (pep_link, pep_status, expected_status)
            )
        pep_statuses[pep_status] = pep_statuses.get(pep_status, 0) + 1

    log_mismatched_statuses(mismatched_statuses)
    return ('Статус', 'Кол-во'), *pep_statuses.items(), ('Всего', len(peps))


def get_expected_status(status):
    return EXPECTED_STATUS.get(status[1:], 'Some unknown status')


def log_mismatched_statuses(mismatched_statuses):
    mismatched_message = ['Несовпадающие статусы:']
    for status in mismatched_statuses:
        mismatched_message.append(
            (f'\n{status[0]}\n'
             f'Статус в карточке: {status[1]}\n'
             f'Ожидаемые статусы: {status[2]}')
        )
    logger.info(''.join(mismatched_message))


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    logger.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logger.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)
    logger.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
