#-*- coding: utf-8 -*-

# 내장 라이브러리
import os

# 서드파티 라이브러리
import gspread
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
    doc = gc.open_by_url(spreadsheet_url) # 스프레스시트 문서 가져오기 
    worksheet = doc.worksheet(spreadsheet_name) # 시트 선택하기
    return worksheet


# 서드파티 라이브러리
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def authorize_v2_experimental():
    """API 문서가 변경되었는지 모르겠는데, 
    https://developers.google.com/sheets/api/quickstart/python
    에 따르면 아래와 같은 가이드를 사용하도록 권하고 있습니다.
    그럼 난 도대체 뭘 본거지?

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