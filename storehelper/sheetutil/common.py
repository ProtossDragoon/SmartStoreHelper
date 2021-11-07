#-*- coding: utf-8 -*-

# 내장 라이브러리
import os
from datetime import date

# 서드파티 라이브러리
import gspread
from gspread import WorksheetNotFound
from oauth2client.service_account import ServiceAccountCredentials

# 우리 프로젝트
from storehelper.metadata.tool import get_json_meatadata


def authorize():
    meta = get_json_meatadata()
    print(f"{os.path.abspath(meta['CREDENTIAL_FILE_PATH_PATH'])}")
    gc = gspread.authorize(
        ServiceAccountCredentials.from_json_keyfile_name(
            os.path.abspath(meta['CREDENTIAL_FILE_PATH_PATH']), 
            meta['API_SCOPE'])
    )
    return gc


def get_sheet(gc, spreadsheet_url, spreadsheet_name):
    meta = get_json_meatadata()
    doc = get_document(gc, spreadsheet_url)
    try:
        worksheet = doc.worksheet(spreadsheet_name) # 시트 선택하기
    except WorksheetNotFound:
        worksheet = doc.add_worksheet(
            title=spreadsheet_name,
            rows="1000", cols="10")
            # 최대치가 있으므로 주의해야 한다.
    return worksheet


def get_document(gc, spreadsheet_url):  
    doc = gc.open_by_url(spreadsheet_url) # 스프레스시트 문서 가져오기 
    return doc


def remove_sheet(gc, spreadsheet_url, spreadsheet_name):
    doc = get_document(gc, spreadsheet_url)
    doc.del_worksheet(get_sheet(gc, spreadsheet_url, spreadsheet_name))


# 서드파티 라이브러리
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def authorize_v2_experimental():
    """API 문서가 변경되었는지 모르겠는데, 
    https://developers.google.com/sheets/api/quickstart/python
    에 따르면 아래와 같은 가이드를 사용하도록 권하고 있습니다.
    # NOTE : 이것은 low level REST API 이고, 
    # 우리가 사용하기 편한 python api 는
    # `gspread` 입니다.

    Returns:
        sheet : 스프레드시트 객체입니다.
    """
    meta = get_json_meatadata()
    creds = Credentials.from_authorized_user_file(
        meta['CREDENTIAL_FILE_PATH_PATH'], 
        meta['API_SCOPE'])
    
    # If there are no (valid) credentials available, 
    # let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                meta['CREDENTIAL_FILE_PATH_PATH'], 
                meta['API_SCOPE'])
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(meta['CREDENTIAL_FILE_PATH_PATH'], 'w') as token:
            token.write(creds.to_json())
    
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    return sheet


def range_reader(ws, gs_meta, name):
    """형식이 
    [<name>][range][start_row]
    [<name>][range][start_col]
    [<name>][range][end_row]
    [<name>][range][end_col]
    과 같다면 다 읽어들일 수 있습니다.
    """
    r_index_start = (
        gs_meta[f'{name}']['range']['start_col']
        + str(gs_meta[f'{name}']['range']['start_row']))
    r_index_end   = (
        gs_meta[f'{name}']['range']['end_col'] + 
        str(gs_meta[f'{name}']['range']['end_row']))
    r_range = f'{r_index_start}:{r_index_end}'
    r_cells = ws.range(r_range)
    print(f'range : {r_index_start}:{r_index_end}')
    print(f'total {repr(len(r_cells))} cells')

    return r_cells