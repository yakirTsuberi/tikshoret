import datetime
import argparse
from pathlib import Path

import xlsxwriter
from utils import get_my_sales


def write_to_excel(agent, date) -> Path:
    date = date.split('-')
    date_filter = datetime.datetime(int(date[1]), int(date[0]), 1)
    path = str(Path.home() / 'FlaskApp' / 'FlaskApp' / 'static' / 'excel_tmp' / (agent + '.xlsx'))
    workbook = xlsxwriter.Workbook(path)
    worksheet = workbook.add_worksheet()
    data = {'חברה': [], 'מסלול': [], 'לקוח': [], 'ת.ז.': [], 'טלפון': [], 'סים': [], 'תאריך': []}
    row = 0
    col = 0
    for i in get_my_sales('yishaiphone-prodaction', agent, date_filter):
        data['חברה'].append(i[0].company)
        data['מסלול'].append(i[0].name)
        data['לקוח'].append(i[1].first_name + ' ' + i[1].last_name)
        data['ת.ז.'].append(i[1].client_id)
        data['טלפון'].append(i[4])
        data['סים'].append(i[3])
        data['תאריך'].append(i[2])
    for key in data.keys():
        worksheet.write(row, col, key)
        for item in data[key]:
            row += 1
            worksheet.write(row, col, item)
        col += 1
    workbook.close()
    return Path(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--agent", help="fully automatized upgrade")
    parser.add_argument("-d", "--date", help="fully automatized upgrade")
    args = parser.parse_args()
    write_to_excel(agent=args.agent, date=args.date)
