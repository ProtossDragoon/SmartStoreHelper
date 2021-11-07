# 내장 라이브러리
import os
import pprint
import time
import shutil
import pathlib
import glob
import json
from datetime import date
from itertools import product, permutations, combinations_with_replacement
from gspread.exceptions import APIError

# 서드파티
import numpy as np
import pandas as pd
import requests
from requests.api import head

# 우리 프로젝트
from .common import read_json, get_latest_file_as_df
from storehelper.metadata import tool
from storehelper.searchad import signaturehelper
from storehelper.crawlutil.common import ChromeDriverManager
from storehelper.sheetutil.common import authorize, get_sheet, remove_sheet, range_reader
from storehelper.sheetutil.reader import generate_list_matrix
from storehelper.sheetutil.writer import overwrite_entire_dataframe


class PowerLinkManager():
    
    def __init__(self,
        dummy_save_dir:str,
        customer_id:str=None,
    )->None:
        self.dummy_save_dir = dummy_save_dir
        if customer_id is None:
            customer_ids = tool.get_json_meatadata()['NAVER_ADS_CREDENTIAL']
            self.customer_id = list(customer_ids.keys())[-1] # last one
        else:
            self.customer_id = customer_id

        def read_api_key():
            _p = tool.get_json_meatadata()['NAVER_ADS_CREDENTIAL'][self.customer_id]['ACCESS_LICENSE_TXT_PATH']
            with open(_p, mode='r') as f:
                return f.readline()
            
        def read_secret_key():
            _p = tool.get_json_meatadata()['NAVER_ADS_CREDENTIAL'][self.customer_id]['SECRET_KEY_TXT_PATH']
            with open(_p, mode='r') as f:
                return f.readline()
        
        self._api_key = read_api_key()
        self._secret_key = read_secret_key()
        self.campaign_info = {}
        self.adgroup_info = {}

    def close(self,):
        with open(os.path.join(self.dummy_save_dir, 'campaign_info.json'), 'w', encoding='UTF-8-sig') as f:
            json.dump(self.campaign_info, f, indent=4, ensure_ascii=False)
        with open(os.path.join(self.dummy_save_dir, 'adgroup_info.json'), 'w', encoding='UTF-8-sig') as f:    
            json.dump(self.adgroup_info, f, indent=4, ensure_ascii=False)

    def get_header(self,
        method:str, 
        uri:str,
    )->dict:
        """샘플 코드에서 서버에 응답을 요청할 때마다 헤더를 생성해주는 역할을 합니다. 
        naver 이 제공한 전체 샘플 코드의 중하단부를 살펴보면, 
        각각의 서비스를 요청할 때 사용되는 requests 모듈에 
        headers 매개변수의 값으로 사용된 것을 확인할 수 있습니다.

        Args:
            method (str): [description]
            uri (str): [description]

        Returns:
            dict: [description]
        """

        timestamp = str(round(time.time() * 1000))
        signature = signaturehelper.Signature.generate(
            timestamp, method, uri, self._secret_key)
        
        return {
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Timestamp': timestamp,
            'X-API-KEY': self._api_key,
            'X-Customer': self.customer_id,
            'X-Signature': signature,
            }

    def get_unique_campaign_name(self, campaign_name:str):
        if not self.campaign_info.get(campaign_name, 0):
            self.campaign_info[campaign_name] = {}
        i = self.campaign_info[campaign_name].get('number', 0)
        self.campaign_info[campaign_name]['number'] = i + 1 # 1부터 시작함.
        return f'{campaign_name}_{i+1}'

    def get_unique_adgroup_name(self, adgroup_name:str):
        if not self.adgroup_info.get(adgroup_name, 0):
            return f'{adgroup_name}_1'
        else:
            li = []
            for i in list(self.adgroup_info[adgroup_name].keys()):
                li.append(int(i))
            i = max(li)
            return f'{adgroup_name}_{int(i+1)}'
            
    def create_campaign(self, 
        campaign_name:str,
        daily_budget:int=10000,
        print_status_code=True,
        print_response_body=True
    )->str:
        # 한 개의 계정마다 100,000 개의 키워드를 등록할 수 있습니다.
        # 한 개의 캠페인마다 100,000 개의 키워드를 등록할 수 있습니다.
        # https://naver.github.io/searchad-apidoc/#/operations/POST/~2Fncc~2Fcampaigns
        _internal_campaign_name = self.get_unique_campaign_name(campaign_name)
        _data = {
            'campaignTp':'WEB_SITE',
            'dailyBudget':daily_budget,
            'deliveryMethod':'ACCELERATED',
            'name':f'{_internal_campaign_name}',
            'customerId':f'{self.customer_id}', # https://github.com/naver/searchad-apidoc/issues/468
            'periodEndDt':'',
            'periodStartDt':'',
            'trackingMode':'AUTO_TRACKING_MODE',
            'trackingUrl':'',
            'useDailyBudget':'',
            'usePeriod':'',
            'userLock':''
        }
        _uri = '/ncc/campaigns'
        r = requests.post(
            'https://api.naver.com'+_uri,
            #data=json.dumps(data),
            json=_data,
            headers=self.get_header('POST', _uri)
            )
    
        if r.status_code >= 400:
            raise ValueError(r.json())

        if print_status_code:
            pprint.pprint(f'response status_code = {r.status_code}')
        if print_response_body:
            pprint.pprint(f'response body = {r.json()}')
        
        campaign_id = r.json()['nccCampaignId']
        self.campaign_info[campaign_name]['campaign_id'] = campaign_id
        time.sleep(0.3) # api 에게 너무 빠르게 요청보내지 않도록 딜레이
        return campaign_id

    def get_campaign_info(self,
        campaign_id:str,
        print_status_code=True,
        print_response_body=True
    )->None:
        _uri = '/ncc/campaigns'
        r = requests.get(
            'https://api.naver.com'+_uri,
            params={
                'ids':campaign_id
            },
            headers=self.get_header('GET', _uri)
        )
        if print_status_code:
            pprint.pprint(f'response status_code = {r.status_code}')
        if print_response_body:
            pprint.pprint(f'response body = {r.json()}')
        return 

    def create_adgroup(self,
        campaign_id:str,
        adgroup_name:str,
        pc_channel_id:str,
        mobile_channel_id:str,
        media_pc:bool=True,
        media_mobile:bool=True,
        max_cpc:int=70,
        max_cpc_content:int=70,
        daily_budget:int=10000,
        print_status_code=True,
        print_response_body=True,
    )->str:
        # 한 개의 광고그룹마다 키워드 최대 1000 개를 등록할 수 있습니다.

        assert max_cpc >= 70 and max_cpc < 10000

        _inertial_adgroup_name = self.get_unique_adgroup_name(adgroup_name)
        
        _data = {
            'customerId':f'{self.customer_id}', # https://github.com/naver/searchad-apidoc/issues/468
            'adRollingType':'PERFORMANCE', # 소재 노출방식, 컨텐츠 배치 요령 (ROUND_ROBIN, PERFORMANCE)
            'adgroupType':'WEB_SITE', # WEB_SITE, SHOPPING, ... # 정보관리 > 비즈채널 관리 와 맞으면 됨.
            'bidAmt':max_cpc,
            'budgetLock':False,
            'contentsNetworkBidAmt':max_cpc_content,
            'dailyBudget':daily_budget,
            'keywordPlusWeight':'',
            'mobileChannelId':mobile_channel_id, # 정보관리 > 비즈채널 관리
            'mobileNetworkBidWeight':100,
            'name':_inertial_adgroup_name,
            'nccCampaignId':campaign_id,
            'pcChannelId':pc_channel_id, # 정보관리 > 비즈채널 관리
            'pcNetworkBidWeight':100,
            'targets':[
                { # TIME_WEEKLY_TARGET. A targeting type for Time Targeting.
                    'targetTp':'TIME_WEEKLY_TARGET',
                    'target':{
                        # Ads to be shown always. This is exactly the same with to set 'target' as null.
                        "SUN":16777215,
                        "MON":16777215,
                        "TUE":16777215,
                        "WED":16777215,
                        "THU":16777215,
                        "FRI":16777215,
                        "SAT":16777215
                    }
                },
                { # REGIONAL_TARGET. A targeting type for Location Targeting.
                    'targetTp':'REGIONAL_TARGET',
                    'target':{
                        'location':{
                            "KR":["01","02","03","04","05","06","07","08","09","10", "11","12","13","14","15","16","17"],
                            'OTHERS':[] #NOTE: 해외 차단
                        }
                    }
                },
                { # MEDIA_TARGET. A targeting type for Media Targeting.
                    'targetTp':'MEDIA_TARGET',
                    'target':{
                        "type":2,
                        "search":[
                            "naver", 
                            #"partner" #NOTE: 파트너 검색엔진 차단
                        ],
                        "contents":[
                            "naver", #NOTE: 네이버 컨텐츠 차단
                            "partner" #NOTE: 파트너 컨텐츠 차단
                        ],
                        'black':{
                            'media':[],
                            'mediaGroup':[],
                        }
                    }
                },
                { # PC_MOBILE_TARGET. A targeting type for PC/Mobile Targeting.
                    'targetTp':'PC_MOBILE_TARGET',
                    'target':{
                        "pc":media_pc, #NOTE: pc 노출
                        "mobile":media_mobile, #NOTE: 모바일 노출
                    }
                }
            ],
            'useKeywordPlus':True, # 키워드 확장
        }

        _uri = '/ncc/adgroups'
        r = requests.post(
            'https://api.naver.com'+_uri,
            #data=json.dumps(data),
            json=_data,
            headers=self.get_header('POST', _uri)
            )
    
        if print_status_code:
            pprint.pprint(f'response status_code = {r.status_code}')
        if print_response_body:
            pprint.pprint(f'response body = {r.json()}')

        if r.status_code >= 400:
            raise ValueError(r.json())

        adgroup_id = r.json()['nccAdgroupId']
        self.record_adgroup_info(adgroup_name, adgroup_id, campaign_id)
        time.sleep(0.3) # api 에게 너무 빠르게 요청보내지 않도록 딜레이
        return adgroup_id

    def record_adgroup_info(self, 
        adgroup_name, 
        adgroup_id, 
        campaign_id
    )->None:

        def get_latest_number():
            # 그냥 가장 큰 수에다가 1 더해서 가져오는 로직
            li = []
            for i in self.adgroup_info[adgroup_name].keys():
                li.append(int(i))
            return max(li)+1

        if self.adgroup_info.get(adgroup_name, 0):
            #FIXME "1" 대신 적절한 숫자를 넣을 것
            _number = get_latest_number()
            self.adgroup_info[adgroup_name][f"{_number}"] = {
                'adgroup_id':adgroup_id,
                'campaign_id':campaign_id,
            }
        else:
            self.adgroup_info[adgroup_name] = {
                "1":{
                    'adgroup_id':adgroup_id,
                    'campaign_id':campaign_id,
                }
            }

    def create_ad(self,
        headline:str,
        description:str,
        adgroup_id:str,
        media_pc:bool=True,
        media_mobile:bool=True,
        mobile_link:str=None,
        pc_link:str=None,
        print_status_code=True,
        print_response_body=False,
    )->str:

        if media_pc:
            assert pc_link, f'mobile_link, pc_link 둘 중 하나는 입력해야 해요!'
        if media_mobile:
            assert mobile_link, f'mobile_link, pc_link 둘 중 하나는 입력해야 해요!'

        _data = {
            'ad':{
                'pc':{'final':''},
                'mobile':{'final':''},
                "headline": headline,
                "description": description,
            },
            'inspectRequestMsg':'none',
            'nccAdgroupId':adgroup_id,
            'type':'TEXT_45', # 파워링크의 웹사이트 광고같은 경우에는 TEXT_45 인듯함.
            'userLock':False,
            'customerId':f'{self.customer_id}', # https://github.com/naver/searchad-apidoc/issues/468
        }
        if media_mobile:
            _data['ad']['mobile'] = {'final':f'{mobile_link}'}
        if media_pc:
            _data['ad']['pc'] = {'final':f'{pc_link}'}
        if not media_mobile:
            _data['ad']['mobile'] = {'final':f'{pc_link}'}
        if not media_pc:
            _data['ad']['pc'] = {'final':f'{mobile_link}'}

        _uri = '/ncc/ads'
        r = requests.post(
            'https://api.naver.com'+_uri,
            #data=json.dumps(data),
            json=_data,
            headers=self.get_header('POST', _uri)
            )
    
        if print_status_code:
            pprint.pprint(f'response status_code = {r.status_code}')
        if print_response_body:
            pprint.pprint(f'response body = {r.json()}')

        if r.status_code >= 400:
            raise ValueError(r.json())

        ad_id = r.json()['nccAdId']
        time.sleep(0.1) # api 에게 너무 빠르게 요청보내지 않도록 딜레이
        return ad_id

    def create_adkeyword(self,
        adgroup_id:str, *,
        keyword:str=None,
        keyword_list:list=None,
        print_status_code=True,
        print_response_body=False,
    )->None:

        if keyword:
            assert not keyword_list, '하나만 해'
        if keyword_list:
            assert not keyword, '하나만 해'

        def get_ad_keyword(_keyword:str):
            _ad_keyword_form = {
                #'bidAmt':bid, #NOTE : 이거 넣으면 작동 안함 망할...
                'keyword':_keyword.replace(' ', ''),
            }            
            return _ad_keyword_form

        if keyword:
            _data = [get_ad_keyword(keyword)]
        if keyword_list:
            _data = [get_ad_keyword(e) for e in keyword_list]

        _uri = '/ncc/keywords'
        r = requests.post(
            'https://api.naver.com'+_uri,
            #data=json.dumps(data),
            params={'nccAdgroupId':adgroup_id},
            json=_data,
            headers=self.get_header('POST', _uri)
            )
    
        if print_status_code:
            pprint.pprint(f'response status_code = {r.status_code}')
        if print_response_body:
            pprint.pprint(f'response body = {r.json()}')

        if r.status_code >= 400:
            raise ValueError(r.json())

        time.sleep(0.01) # api 에게 너무 빠르게 요청보내지 않도록 딜레이
        return None

def run(
    ad_meta, biz_ch_meta,
    gs_meta, gs_r_meta,
    cdm, chrome_driver, chrome_download_dir
):
    # 데이터를 구글 스프레드시트서 읽어옵니다.
    gc = authorize()
    ws_r = get_sheet(gc, 
        spreadsheet_url=gs_r_meta['url'],
        spreadsheet_name=gs_r_meta['name'])

    campaign_name_cells = range_reader(ws_r, gs_r_meta, 'campaign_name')
    adgroup_name_cells = range_reader(ws_r, gs_r_meta, 'adgroup_name')
    ads_headline_cells = range_reader(ws_r, gs_r_meta, 'ads_headline')
    ads_description_cells = range_reader(ws_r, gs_r_meta, 'ads_description')
    adgroup_config_pc_cells = range_reader(ws_r, gs_r_meta, 'adgroup_config_pc')
    adgroup_config_mobile_cells = range_reader(ws_r, gs_r_meta, 'adgroup_config_mobile')
    
    plm = PowerLinkManager(chrome_download_dir)

    for (cmp_c, adg_c, adh_c, add_c, conf_pc, conf_mb) in zip(
        campaign_name_cells,
        adgroup_name_cells,
        ads_headline_cells,
        ads_description_cells,
        adgroup_config_pc_cells,
        adgroup_config_mobile_cells):
        if len(cmp_c.value) == 0:
            continue
        
        # campaign (캠페인)
        campaign_id = plm.create_campaign(f'{cmp_c.value}')

        adk_r = get_sheet(gc, 
            spreadsheet_url=gs_r_meta['url'],
            spreadsheet_name=cmp_c.value
        )
        adkeyword_cells = range_reader(adk_r, gs_r_meta, 'adkeyword_in_campaign')

        i = 0
        keyword_li = []
        for adk_c in adkeyword_cells:
            if len(adk_c.value) == 0:
                continue
            if i % 1000 == 0:
                print(f'{repr(bool(conf_pc.value)), repr(bool(conf_mb.value))}')
                _is_pc_media = bool(conf_pc.value)
                _is_mobile_media = bool(conf_mb.value)
                # 키워드 1000 개마다 adgroup (광고그룹) 생성
                adgroup_id = plm.create_adgroup(
                    campaign_id, f'{adg_c.value}',
                    biz_ch_meta['hellocock_smartstore']['ID'],
                    biz_ch_meta['hellocock_smartstore']['ID'],
                    media_pc=_is_pc_media,
                    media_mobile=_is_mobile_media,)

                _ = plm.create_ad(
                    adh_c.value,
                    add_c.value,
                    adgroup_id,
                    media_pc=_is_pc_media,
                    media_mobile=_is_mobile_media,
                    pc_link=biz_ch_meta['hellocock_smartstore']['URL'],
                    mobile_link=biz_ch_meta['hellocock_smartstore']['URL'],
                )
        
            # 리스트로 등록
            keyword_li.append(adk_c.value)
            if i % 100 == 99:
                # 등록
                plm.create_adkeyword(adgroup_id, keyword_list=keyword_li)
                keyword_li = []

            # 플레인하게 등록
            # plm.create_adkeyword(adgroup_id, keyword=adk_c.value)                
            i += 1

    cdm.chrome_close_safely()
    plm.close()


if __name__ == '__main__':
    ad_meta = read_json(filename=pathlib.Path(__file__).stem)['naver_ads']
    biz_ch_meta = ad_meta['buisness_channel']
    gs_meta = read_json(filename=pathlib.Path(__file__).stem)['google_spreadsheet']
    gs_r_meta = gs_meta['read_keyword']

    cdm = ChromeDriverManager()
    cdm.set_default_download_dir(pathlib.Path(__file__).stem, join=True)
    cdm.set_secure_mode(False)
    chrome_driver = cdm.get_chrome_driver()
    chrome_download_dir = cdm.get_default_download_dir()
    run(
        ad_meta, biz_ch_meta,
        gs_meta, gs_r_meta,
        cdm, chrome_driver, chrome_download_dir
    )