#-*- coding: utf-8 -*-

"""
크롤러와 관련해서 자주 사용하는 유틸 함수들을 모아 두었습니다.

<설계 원칙>
크롬 파일 다운로드 경로는 전역 변수라고 생각하면 좋습니다.
그만큼 직접 다루거나 잘못 다루면 오류의 위험이 많기 때문에,
getter 과 setter 을 이용하기를 권장합니다.

<FIXME>
chrome driver 의 option 관련 설정은 시작 시에 한번만 설정이 가능하고
option 을 변경하면 크롬드라이버 객체도 변경됩니다.
이렇게 전역적 요소이기 때문에 다른 파일로부터 세팅할 수 있도록 해야합니다.
지금 굉장히 꼬임 ㅠㅠ
클래스를 통해 상태관리가 가능하도록 해야 합니다.
"""

# 내장 라이브러리
import time
import os
import logging

# 서드파티
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options  

# 우리 프로젝트
from storehelper.metadata.tool import get_json_meatadata
from storehelper.metadata import _CHROME_DRIVER as chrome_driver
from storehelper.metadata import _CHROME_DOWNLOAD_DIR as chrome_download_dir 
from storehelper.metadata import _CHROME_OPTIONS as chrome_options
from storehelper.metadata import _CHROME_DRIVER_PATH as chrome_driver_path

class ChromeDriverManager:

    def __init__(
        self,
        json_path:str='./storehelper/metadata/template.json',
    )->None:
        _dic = get_json_meatadata(json_path)
        self._mem_chrome_driver_path = None
        self._mem_default_download_dir = None
        self._mem_headless_mode = None
        self._cached_chrome_driver_li = []

        self._chrome_driver_path = self._mem_chrome_driver_path = os.path.abspath(_dic['CHROME_DRIVER_PATH'])
        self._default_download_dir = _dic['DOWNLOADING_FILE_DIR']
        self._headless_mode = self._mem_headless_mode = False
        
    def _warning_driver_status(self):
        """chrome driver 은 option 이 변경될 때마다 다시 생성해주어야 합니다. 
        옵션이 변경되었는데 get_chrome_driver 이 호출되지 않은 경우
        이 함수는 경고를 출력합니다.
        """
        print(f'가장 마지막에 get_chrome_driver 을 호출한 시점의 정보입니다.')
        self._check_same(
            mem_val=self._mem_chrome_driver_path,
            val=self._chrome_driver_path)
        self._check_same(
            mem_val=self._mem_default_download_dir,
            val=self._default_download_dir)
        self._check_same(
            mem_val=self._mem_headless_mode,
            val=self._headless_mode)

    def _check_same(self, *, 
        mem_val=None, 
        val=None,
        warning:bool=True,
        raise_error:bool=False
    )->bool:
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
        self._headless_mode = val
        self._warning_driver_status()

    def set_default_download_dir(self, path:str):
        self._default_download_dir = path
        self._warning_driver_status()
    
    def get_chrome_driver(self, new=False):
        cond = set({})
        cond.add(self._check_same(
            self._mem_chrome_driver_path,
            self._chrome_driver_path,
            warning=False))
        cond.add(self._check_same(
            self._mem_default_download_dir,
            self.default_download_dir,
            warning=False))
        cond.add(self._check_same(
            self._mem_headless_mode,
            self.headless_mode,
            warning=False))

        if False in cond: # 하나라도 다르면
            self._mem_chrome_driver_path = self._chrome_driver_path
            self._mem_default_download_dir = self.default_download_dir
            self._mem_headless_mode = self.headless_mode
            prefs = {'download.default_directory':self._default_downlaod_dir}
            _chrome_options = webdriver.ChromeOptions()
            _chrome_options.add_experimental_option('prefs', prefs)
            chrome_driver = webdriver.Chrome(
                    self._mem_chrome_driver_path,
                    chrome_options=_chrome_options,
                    )
            if self._mem_headless_mode:
                chrome_driver.add_argument("--headless")
                chrome_driver.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            self._cached_chrome_driver_li.append(chrome_driver)
            return chrome_driver
        else: # 모두 다 변한 것이 없다면
            if new: # 그럼에도 새로운 드라이버를 원한다면
                prefs = {'download.default_directory':self._mem_default_download_dir}
                _chrome_options = webdriver.ChromeOptions()
                _chrome_options.add_experimental_option('prefs', prefs)
                new_chrome_driver = webdriver.Chrome(
                    self._mem_chrome_driver_path,
                    chrome_options=_chrome_options,
                    )
                self._cached_chrome_driver_li.append(new_chrome_driver)
                return new_chrome_driver
            else:
                return self._cached_chrome_driver_li[-1]
    
    def get_default_download_dir(self):
        return self._mem_default_download_dir

    def get_headless_mode_info(self):
        return self._mem_headless_mode

    def get_chrome_driver_path(self):
        return self._mem_chrome_driver_path

    def chrome_close_safely(self):
        """안전하게 크롬 드라이버를 종료합니다.
        """
        print('3초 후에 크롬 드라이버를 완전히 종료합니다.')
        time.sleep(3)
        for chrome_driver in self.chrome_driver_li:
            chrome_driver.close()
            chrome_driver.quit()


def chrome_close_safely():
    """안전하게 크롬 드라이버를 종료합니다.
    """
    print('3초 후에 크롬 드라이버를 완전히 종료합니다.')
    time.sleep(3)
    chrome_driver.close()
    chrome_driver.quit()


def set_chrome_headless_mode():
    """크롬 드라이버를 실행할 때 실행해야 합니다.
    """
    chrome_driver.add_argument("--headless")
    chrome_driver.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    # FIXME 이것만으로 되는 게 아님
    

def set_chrome_default_download_dir(dir:str):
    """크롬 파일 다운로드 경로를 재설정합니다.

    Args:
        dir (str): 경로
    """
    # FIXME deprecated
    global chrome_download_dir
    if os.path.exists(dir):
        # 존재하면 경로인지 아닌지 확인해야 합니다.
        assert os.path.isdir(dir), f'{dir} 은 디렉터리가 아닙니다.'
    else:
        # 존재하지 않는다면 생성합니다.
        os.makedirs(dir, exist_ok=False)

    chrome_download_dir = dir
    print(f'다운로드 경로를 {repr(chrome_download_dir)} 로 설정합니다.')
    
    _chrome_options = Options()
    _chrome_options.add_argument()


def set_with_join_chrome_default_download_dir(additional_dir:str):
    """크롬 파일 다운로드 경로를, 크롬 다운로드 기본경로에 추가적인 경로를 붙여 변경합니다.

    Args:
        additional_dir (str): 경로
    """
    # FIXME deprecated
    p = os.path.join(get_chrome_default_download_dir(), additional_dir)
    set_chrome_default_download_dir(p)


def get_chrome_default_download_dir():
    """크롬 파일 다운로드 경로에 대한 Getter 입니다/

    Returns:
        str: 크롬 파일 다운로드 경로
    """
    # FIXME deprecated
    global chrome_download_dir
    return chrome_download_dir


def wait_for_downloads_v2(
    file_download_dir:str=None,
    headless:bool=False, 
    num_files:int=1,
    driver=chrome_driver,
)->None:
    #FIXME : 클래스 메소드로 만들어주자.
    """파일을 다운로드해서, 파일을 읽고 써야 하는 작업이 파일 다운로드 결과에 종속적이라면
    파일 다운로드를 완전히 잘 마칠 때까지 안전하게 대기할 줄 기능이 필요합니다.
    이 함수는 크롬 드라이버가 파일을 완전히 다운로드받을 때까지 대기합니다.

    Args:
        file_download_dir (str, optional): 크롬 드라이버의 파일 다운로드 경로를 입력합니다. 
            지정하지 않는 경우 기본값이 적용됩니다. 
            Defaults to None.
        headless (bool, optional): 일부 크롬 드라이버의 경우 headless 상태로 실행됩니다. 
            MAC 에서는 이것을 True 로 할 수 없다고 합니다. 
            Defaults to False.
        num_files (int, optional): 다운로드받는 파일의 개수입니다. 
            Defaults to 1.
        driver (chrome_driver, optional): 크롬 드라이버 객체입니다. 
            Defaults to chrome_driver.
    """
    if file_download_dir:
        file_download_dir = get_chrome_default_download_dir()
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

        driver.execute_script("window.open();")
        driver.switch_to.window(driver.window_handles[1])
        driver.get('chrome://downloads/')
        # Wait for downloads to complete
        WebDriverWait(driver, max_delay, interval_delay).until(lambda d: all_downloads_completed(d, num_files))
        # Clear all downloads from chrome://downloads/
        driver.execute_script("""
            document.querySelector('downloads-manager').shadowRoot
            .querySelector('#toolbar').shadowRoot
            .querySelector('#moreActionsMenu')
            .querySelector('button.clear-all').click()
            """)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])


def scroll_page_down(
    driver=chrome_driver,
    delay:int=1,
)->None:
    """If you want to scroll to a page with infinite loading,
    like social network ones, facebook etc. (thanks to @Cuong Tran)
    네이버 쇼핑과 같은 경우에도, 스크롤을 내려야 다음것이 로드되는 구조를 가지고 있습니다.
    많은 웹사이트에서 이와 같은 구조를 이루고 있기 때문에 
    잠시 기다렸다가 다시 내려주는 로직이 필요합니다.
    """
    SCROLL_PAUSE_TIME = delay

    # Get scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(SCROLL_PAUSE_TIME)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height