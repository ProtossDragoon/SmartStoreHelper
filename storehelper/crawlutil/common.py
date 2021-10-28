#-*- coding: utf-8 -*-

"""
크롤러와 관련해서 자주 사용하는 유틸 함수들을 모아 두었습니다.

<설계 원칙>
크롬 파일 다운로드 경로는 전역 변수라고 생각하면 좋습니다.
그만큼 직접 다루거나 잘못 다루면 오류의 위험이 많기 때문에,
getter 과 setter 을 이용하기를 권장합니다.
chrome driver 의 option 관련 설정은 시작 시에 한번만 설정이 가능하고
option 을 변경하면 크롬드라이버 객체도 변경됩니다.
이렇게 전역적 요소이기 때문에 다른 파일로부터 세팅할 수 있도록 해야합니다.
클래스를 통해 상태관리가 가능하도록 합니다.

<TODO>
클린 코드는 아닙니다.
리스트로 하드코딩되어 있는 내용들은 유지보수 과정에서
코드를 읽는 데 어려움을 줄 수 있기 때문에 제거해야 합니다.
"""

# 내장 라이브러리
import time
import os
import logging

# 서드파티
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options  

# 우리 프로젝트
from storehelper.metadata.tool import get_json_meatadata

class ChromeDriverManager:

    def __init__(
        self,
        json_path:str='./storehelper/metadata/template.json',
    )->None:
        _dic = get_json_meatadata(json_path)

        # containers
        self._mem_chrome_driver_path = []
        self._mem_default_download_dir = []
        self._mem_headless_mode = []
        self._mem_window_w = []
        self._mem_window_h = []

        self._chrome_driver_path = []
        self._default_download_dir = []
        self._headless_mode = []
        self._window_w = []
        self._window_h = []
        
        self._cached_chrome_driver_li = []

        # init
        self._mem_chrome_driver_path.append(os.path.abspath(_dic['CHROME_DRIVER_PATH']))
        self._chrome_driver_path.append(os.path.abspath(_dic['CHROME_DRIVER_PATH']))

        _p = os.path.abspath(_dic['DOWNLOADING_FILE_DIR'])
        self._mem_default_download_dir.append(_p)
        self._default_download_dir.append(_p)

        # 백그라운드 모드
        self._mem_headless_mode.append(False)
        self._headless_mode.append(False) 

        # 창 크기
        self._mem_window_w.append(False)
        self._window_w.append(False)
        self._mem_window_h.append(False)
        self._window_h.append(False)
        
    def _warning_driver_status(self):
        """chrome driver 은 option 이 변경될 때마다 다시 생성해주어야 합니다. 
        옵션이 변경되었는데 get_chrome_driver 이 호출되지 않은 경우
        이 함수는 경고를 출력합니다.
        """
        print(f'가장 마지막에 get_chrome_driver 을 호출한 시점의 정보입니다.')
        self._check_same(
            mem_val=self._mem_chrome_driver_path[-1],
            val=self._chrome_driver_path[-1])
        self._check_same(
            mem_val=self._mem_default_download_dir[-1],
            val=self._default_download_dir[-1])
        self._check_same(
            mem_val=self._mem_headless_mode[-1],
            val=self._headless_mode[-1])
        self._check_same(
            mem_val=self._mem_window_h[-1],
            val=self._window_h[-1])
        self._check_same(
            mem_val=self._mem_window_w[-1],
            val=self._window_w[-1])
        print(f'다른 요소가 있다면, get_chrome_driver() 을 통해'
                '업데이트된 크롬 드라이버를 다시 받아오세요.')

    def _check_same(self, mem_val, val,
        warning:bool=True,
        raise_error:bool=False
    )->bool:
        assert mem_val is not None
        assert val is not None
        
        if mem_val != val:
            if warning:
                print(f'{repr(mem_val)} != {repr(val)}')
            if raise_error:
                raise ValueError(f'{repr(mem_val)} != {repr(val)}')
            return False
        else:
            return True

    def set_headless_mode(self, val:bool=False):
        """headless mode 란 background mode 를 의미합니다.
        MAC 에서 headless 를 사용하는 것을 권장하지 않는 분위기입니다.

        Args:
            val (bool, optional): headless mode 를 사용할지 여부입니다. 
                Defaults to False.
        """
        self._headless_mode.append(val)
        self._warning_driver_status()

    def set_chrome_window_size(self, *,
        w:int=None, 
        h:int=None,
    )->None:
        assert w is not None
        assert h is not None
        self._window_w.append(w)
        self._window_h.append(h)

    def set_default_download_dir(self, 
        path:str, *,
        join=False):
        if join:
            # 기존 경로에 조인합니다.
            _p = os.path.join(
                self._default_download_dir[-1], path)
        else:
            # 기존 경로에 조인하지 않습니다.
            _p = path

        if os.path.exists(_p):
            # 존재하면 경로인지 아닌지 확인해야 합니다.
            assert os.path.isdir(_p), f'{_p} 은 디렉터리가 아닙니다.'
        else:
            # 존재하지 않는다면 생성합니다.
            os.makedirs(_p, exist_ok=False)
        
        self._default_download_dir[-1] = _p
        self._warning_driver_status()
    
    def get_chrome_driver(self, new=False):
        cond = set({})
        _a = self._check_same(
            mem_val=self._mem_chrome_driver_path[-1],
            val=self._chrome_driver_path[-1],
            warning=False)
        cond.add(_a)
        _b = self._check_same(
            mem_val=self._mem_default_download_dir[-1],
            val=self._default_download_dir[-1],
            warning=False)
        cond.add(_b)
        _c = self._check_same(
            mem_val=self._mem_headless_mode[-1],
            val=self._headless_mode[-1],
            warning=False)
        cond.add(_c)
        _d = self._check_same(
            mem_val=self._mem_window_h[-1],
            val=self._window_h[-1],
            warning=False)
        cond.add(_d)
        _e = self._check_same(
            mem_val=self._mem_window_w[-1],
            val=self._window_w[-1],
            warning=False)
        cond.add(_e)

        def driver_generation():
            """최근 등록한 정보를 바탕으로 한
            크롬 드라이버 생성 로직 헬퍼 함수

            Returns:
                chrome_driver: 크롬 드라이버를
            """
            prefs = {'download.default_directory':self._default_download_dir[-1]}
            _chrome_options = webdriver.ChromeOptions()
            _chrome_options.add_experimental_option('prefs', prefs)
            if self._mem_headless_mode[-1]:
                _chrome_options.add_argument("--headless")
                _chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            """
            if self._mem_window_h[-1] or self._mem_window_w[-1]:
                print(f'[driver_generation] window size w:{self._mem_window_w[-1]} h:{self._mem_window_h[-1]}')
                _chrome_options.add_argument(f"--window-size={self._mem_window_w[-1]}, {self._mem_window_h[-1]}")
            """
            chrome_driver = webdriver.Chrome(
                    self._mem_chrome_driver_path[-1],
                    chrome_options=_chrome_options)
            if self._mem_window_h[-1] or self._mem_window_w[-1]:
                chrome_driver.set_window_size(
                    width=self._mem_window_w[-1],
                    height=self._mem_window_h[-1])
            self._cached_chrome_driver_li.append(chrome_driver)
            return chrome_driver

        if False in cond: # 기존 드라이버와 달라진 점이 있다면
            self._mem_chrome_driver_path.append(self._chrome_driver_path[-1])
            self._mem_default_download_dir.append(self._default_download_dir[-1])
            self._mem_headless_mode.append(self._headless_mode[-1])
            self._mem_window_h.append(self._window_h[-1])
            self._mem_window_w.append(self._window_w[-1])
            return driver_generation()
        else: # 모두 다 변한 것이 없다면
            if new: # 그럼에도 새로운 드라이버를 원한다면
                return driver_generation()
            else:
                return self._cached_chrome_driver_li[-1]

    def get_default_download_dir(self):
        return self._mem_default_download_dir[-1]

    def get_headless_mode_info(self):
        return self._mem_headless_mode[-1]

    def get_chrome_driver_path(self):
        return self._mem_chrome_driver_path[-1]

    def chrome_close_safely(self):
        """안전하게 크롬 드라이버를 종료합니다.
        """
        print('3초 후에 크롬 드라이버를 완전히 종료합니다.')
        time.sleep(3)
        for chrome_driver in self._cached_chrome_driver_li:
            chrome_driver.close()
            chrome_driver.quit()

    def wait_for_block(self, *,
        id=None,
        chrome_driver=None,
        delay:int=30,
    )->None:
        if chrome_driver is None:
            chrome_driver = self._cached_chrome_driver_li[-1]

        WebDriverWait(chrome_driver, delay).until(
            EC.presence_of_element_located(
                (By.XPATH, f'//*[@id="{id}" and contains(@style, "none")]')
            )
        )

    def wait_for_downloads_v2(
        self,
        num_files:int=1,
        chrome_driver_index=-1,
    )->None:
        """파일을 다운로드해서, 파일을 읽고 써야 하는 작업이 파일 다운로드 결과에 종속적이라면
        파일 다운로드를 완전히 잘 마칠 때까지 안전하게 대기할 줄 기능이 필요합니다.
        이 함수는 크롬 드라이버가 파일을 완전히 다운로드받을 때까지 대기합니다.

        Args:
            num_files (int, optional): 다운로드받는 파일의 개수입니다. 
                Defaults to 1.
            chrome_driver_index (chrome_driver, optional): 크롬드라이버의 인덱스입니다.
                Defaults to 가장 마지막에 만들어진 크롬 드라이버 (-1).
        """
        _i = chrome_driver_index
        chrome_driver = self._cached_chrome_driver_li[_i]
        file_download_dir = self._mem_default_download_dir[_i]
        headless = self._mem_headless_mode[_i]

        max_delay = 60
        interval_delay = 0.5
        if headless:
            total_delay = 0
            done = False
            while not done and total_delay < max_delay:
                files = os.listdir(file_download_dir)
                # Remove system files if present: Mac adds the .DS_Store file
                if '.DS_Store' in files:
                    files.remove('.DS_Store')
                if len(files) == num_files and not [f for f in files if f.endswith('.crdownload')]:
                    done = True
                else:
                    total_delay += interval_delay
                    time.sleep(interval_delay)
            if not done:
                logging.error("File(s) couldn't be downloaded")
        else:
            def all_downloads_completed(driver, num_files):
                return driver.execute_script("""
                    var items = document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList').items;
                    var i;
                    var done = false;
                    var count = 0;
                    for (i = 0; i < items.length; i++) {
                        if (items[i].state === 'COMPLETE') {count++;}
                    }
                    if (count === %d) {done = true;}
                    return done;
                    """ % (num_files))

            chrome_driver.execute_script("window.open();")
            chrome_driver.switch_to.window(chrome_driver.window_handles[1])
            chrome_driver.get('chrome://downloads/')
            # Wait for downloads to complete
            WebDriverWait(chrome_driver, max_delay, interval_delay).until(lambda d: all_downloads_completed(d, num_files))
            # Clear all downloads from chrome://downloads/
            chrome_driver.execute_script("""
                document.querySelector('downloads-manager').shadowRoot
                .querySelector('#toolbar').shadowRoot
                .querySelector('#moreActionsMenu')
                .querySelector('button.clear-all').click()
                """)
            chrome_driver.close()
            chrome_driver.switch_to.window(chrome_driver.window_handles[0])

    def scroll_page_down(
        self,
        chrome_driver=None,
        delay:int=1,
    )->None:
        """If you want to scroll to a page with infinite loading,
        like social network ones, facebook etc. (thanks to @Cuong Tran)
        네이버 쇼핑과 같은 경우에도, 스크롤을 내려야 다음것이 로드되는 구조를 가지고 있습니다.
        많은 웹사이트에서 이와 같은 구조를 이루고 있기 때문에 
        잠시 기다렸다가 다시 내려주는 로직이 필요합니다.
        """
        if chrome_driver is None:
            chrome_driver = self._cached_chrome_driver_li[-1]

        # Get scroll height
        last_height = chrome_driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            chrome_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(delay)

            # Calculate new scroll height and compare with last scroll height
            new_height = chrome_driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def hide_google_ads(
        self,
        chrome_driver=None,
    ):
        """접속한 페이지에서 구글 광고를 숨겨줍니다.
        """
        if chrome_driver is None:
            chrome_driver = self._cached_chrome_driver_li[-1]

        all_iframes = chrome_driver.find_elements_by_tag_name("iframe")
        if len(all_iframes) > 0:
            print("Ad Found\n")
            chrome_driver.execute_script("""
                var elems = document.getElementsByTagName("iframe"); 
                for(var i = 0, max = elems.length; i < max; i++)
                    {
                        elems[i].hidden=true;
                    }
                                """)
            print('Total Ads: ' + str(len(all_iframes)))
        else:
            print('No frames found')