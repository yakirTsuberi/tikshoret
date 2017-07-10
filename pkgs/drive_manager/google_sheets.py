from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


class Sheets:
    scope = 'https://www.googleapis.com/auth/drive'
    client_secret_file = 'client_secrets.json'
    application_name = 'Gama S.M.'
    spreadsheet_id = '1n_ir9nlzpmCFR9v1tSr31lePizRrPL7BlABIwBtkOFc'

    def __init__(self):
        self.credentials = self._get_credentials()
        self.service = self._get_service()

    def _get_credentials(self):
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir, self.client_secret_file)

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.client_secret_file, self.scope)
            flow.user_agent = self.application_name
            credentials = tools.run_flow(flow, store, flags)

            print('Storing credentials to ' + credential_path)
        return credentials

    def _get_service(self):
        http = self.credentials.authorize(httplib2.Http())
        discovery_url = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
        return discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discovery_url)

    def read(self):
        return self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, majorDimension='COLUMNS',
                                                        range='Sheet1').execute().get('values')

    def write(self, values):
        body = {'values': values}
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id, range='Sheet1', valueInputOption='RAW', body=body).execute()


def main():
    s = Sheets()
    print(s.read())


if __name__ == '__main__':
    main()
