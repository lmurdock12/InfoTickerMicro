import os, gc
import adafruit_requests as requests

class OTAUpdater:
    """
    A class to update your MicroController with the latest version from a GitHub tagged release,
    optimized for low power usage.
    """

    def __init__(self, github_repo,network_manager, github_src_dir='', module='', main_dir='main', new_version_dir='next', secrets_file=None, headers={}):
        # self.http_client = HttpClient(headers=headers)
        self.github_repo = github_repo.rstrip('/').replace('https://github.com/', '')
        print("Github repo: ",self.github_repo)
        self.github_src_dir = '' if len(github_src_dir) < 1 else github_src_dir.rstrip('/') + '/'
        print("Github SRC dir: ",self.github_src_dir)

        self.module = module.rstrip('/')
        self.main_dir = main_dir
        self.new_version_dir = new_version_dir
        self.code_file = "code.py"
        self.boot_file = "boot.py"
        # self.secrets_file = secrets_file
        # TODO: This should never be none, and we 
        self.network = network_manager
        pass

    def __del__(self):
        # self.http_client = None
        pass

    def check_for_update_to_install_during_next_reboot(self) -> bool:
        """Function which will check the GitHub repo if there is a newer version available.
        
        This method expects an active internet connection and will compare the current 
        version with the latest version available on GitHub.
        If a newer version is available, the file 'next/.version' will be created 
        and you need to call machine.reset(). A reset is needed as the installation process 
        takes up a lot of memory (mostly due to the http stack)
        Returns
        -------
            bool: true if a new version is available, false otherwise
        """

        # (current_version, latest_version) = self._check_for_new_version()
        # if latest_version > current_version:
        #     print('New version available, will download and install on next reboot')
        #     self._create_new_version_file(latest_version)
        #     return True

        # return False
        pass

    def install_update_if_available_after_boot(self, ssid, password) -> bool:
        """This method will install the latest version if out-of-date after boot.
        
        This method, which should be called first thing after booting, will check if the 
        next/.version' file exists. 
        - If yes, it initializes the WIFI connection, downloads the latest version and installs it
        - If no, the WIFI connection is not initialized as no new known version is available
        """

        # if self.new_version_dir in os.listdir(self.module):
        #     if '.version' in os.listdir(self.modulepath(self.new_version_dir)):
        #         latest_version = self.get_version(self.modulepath(self.new_version_dir), '.version')
        #         print('New update found: ', latest_version)
        #         OTAUpdater._using_network(ssid, password)
        #         self.install_update_if_available()
        #         return True
            
        # print('No new updates found...')
        # return False
        pass

    def install_update_if_available(self) -> bool:
        """This method will immediately install the latest version if out-of-date.
        
        This method expects an active internet connection and allows you to decide yourself
        if you want to install the latest version. It is necessary to run it directly after boot 
        (for memory reasons) and you need to restart the microcontroller if a new version is found.
        Returns
        -------
            bool: true if a new version is available, false otherwise
        """

        (current_version, latest_version) = self._check_for_new_version()
        if latest_version > current_version:
            print('Updating to version {}...'.format(latest_version))
            self._create_new_version_file(latest_version)
            self._download_new_version(latest_version)
        #     self._copy_secrets_file()
            self._delete_old_version()
            self._install_new_version()
            return True
        
        return False

    @staticmethod
    def _using_network(ssid, password):
        # import network
        # sta_if = network.WLAN(network.STA_IF)
        # if not sta_if.isconnected():
        #     print('connecting to network...')
        #     sta_if.active(True)
        #     sta_if.connect(ssid, password)
        #     while not sta_if.isconnected():
        #         pass
        # print('network config:', sta_if.ifconfig())
        pass

    def _check_for_new_version(self):

        current_version = self.get_version(self.modulepath(self.main_dir))
        latest_version = self.get_latest_version()

        print('Checking version... ')
        print('\tCurrent version: ', current_version)
        print('\tLatest version: ', latest_version)
        return (current_version, latest_version)


    def _create_new_version_file(self, latest_version):
        #Creates folder for new version code to go and then creates
        #The updated .version file with the latest version

        self.mkdir(self.modulepath(self.new_version_dir))
        with open(self.modulepath(self.new_version_dir + '/.version'), 'w') as versionfile:
            versionfile.write(latest_version)
            versionfile.close()


    def get_version(self, directory, version_file_name='.version'):
        #Grabs the version (single integer) from a given directory name and file 
        print("Attempting to get the version for directory: ",directory)
        print(os.listdir(directory))
        if version_file_name in os.listdir(directory):
            with open(directory + '/' + version_file_name) as f:
                version = f.read()
                return version
        return '0.0'


    def get_latest_version(self):

        latest_release = None
        while latest_release == None:
            try:
                latest_release = self.network.fetch('https://api.github.com/repos/{}/releases/latest'.format(self.github_repo))
            except RuntimeError as e:
                print("Runtime error: ",e)
                self.network._wifi.esp.reset()
                continue
        
        print(latest_release)
        gh_json = latest_release.json()
        version = None
        try:
            version = gh_json['tag_name']
            print("version is: ", version)
        except KeyError as e:
            raise ValueError(
                "Release not found: \n",
                "Please ensure rlease is marked as 'latest', rather than pre-release \n",
                "github api message: \n {} \n ".format(gh_json)
            )

        return version

    def _download_new_version(self, version):
        print('Downloading version {}'.format(version))
        self._download_all_files(version)
        print('Version {} downloaded to {}'.format(version, self.modulepath(self.new_version_dir)))

        print('Downloading boot.py, code.py version {}'.format(version))
        self._download_main_files(version)
        print('Version {} downloaded to root'.format(version))
              


    def _download_all_files(self, version, sub_dir=''):
        url = 'https://api.github.com/repos/{}/contents{}{}{}?ref=refs/tags/{}'.format(self.github_repo, self.github_src_dir, self.main_dir, sub_dir, version)
        print(url)
        gc.collect() 

        success = False
        file_list = None
        while not success:
            try:
                file_list = self.network.fetch(url)
                success = True
            except RuntimeError as e:
                print("RUNTIME ERROR: ",e)
                continue

        file_list_json = file_list.json()

        for file in file_list_json:
            path = self.modulepath(self.new_version_dir + '/' + file['path'].replace(self.main_dir + '/', '').replace(self.github_src_dir, ''))
            print("new path:", path)
            if file['type'] == 'file':
                gitPath = file['path']
                
                success = False
                while not success:
                    try:
                        print('\tDownloading: ', gitPath, 'to', path)
                        
                        gc.collect()
                        print("mem status: ",gc.mem_free())
                        self.network.wget('https://raw.githubusercontent.com/{}/{}/{}'.format(self.github_repo, version, gitPath),path,chunk_size=500)
                        gc.collect()
                        success = True
                        
                    except RuntimeError as e:
                        print("RUNTIME ERROR: ",e)
                        continue

            elif file['type'] == 'dir':
                print('Creating dir', path)
                self.mkdir(path)
                self._download_all_files(version, sub_dir + '/' + file['name'])
            
            print(self.new_version_dir, "status:")
            self._exists_dir(self.modulepath(self.new_version_dir))

            gc.collect()

        file_list.close()


    def _download_main_files(self, version, sub_dir=''):


        new_code_path = self.modulepath("new_code.py")
        print("new code path: ",new_code_path)
        new_boot_path = self.modulepath("new_boot.py")
        print("new boot path: ",new_boot_path)
        
        success = False
        while not success:
            try:
                print('\tDownloading: boot.py and code.py')
                
                gc.collect()
                print("mem status: ",gc.mem_free())
                self.network.wget('https://raw.githubusercontent.com/{}/{}/code.py'.format(self.github_repo, version),new_code_path,chunk_size=500)
                gc.collect()
                self.network.wget('https://raw.githubusercontent.com/{}/{}/boot.py'.format(self.github_repo, version),new_boot_path,chunk_size=500)
                gc.collect()
                success = True
                
            except RuntimeError as e:
                print("RUNTIME ERROR: ",e)
                continue


            print("root status:")
            os.listdir()

            gc.collect()

          
    def _copy_secrets_file(self):
        # if self.secrets_file:
        #     fromPath = self.modulepath(self.main_dir + '/' + self.secrets_file)
        #     toPath = self.modulepath(self.new_version_dir + '/' + self.secrets_file)
        #     print('Copying secrets file from {} to {}'.format(fromPath, toPath))
        #     self._copy_file(fromPath, toPath)
        #     print('Copied secrets file from {} to {}'.format(fromPath, toPath))
        pass

    def _delete_old_version(self):
        print('Deleting old version at {} ...'.format(self.modulepath(self.main_dir)))
        self._rmtree(self.modulepath(self.main_dir))
        print('Deleted old version at {} ...'.format(self.modulepath(self.main_dir)))
        
        #Remove code.py and root.py in main directory
        os.remove("boot.py")
        os.remove("code.py")



    def _install_new_version(self):
        print('Installing new version at {} ...'.format(self.modulepath(self.main_dir)))
        if self._os_supports_rename():
            print("SUPPORTS RENAMING")
            os.rename(self.modulepath(self.new_version_dir), self.modulepath(self.main_dir))
        else:
            print("MANUALLY COPYING")
            self._copy_directory(self.modulepath(self.new_version_dir), self.modulepath(self.main_dir))
            self._rmtree(self.modulepath(self.new_version_dir))

        #Rename the code.py and boot.py files
        os.rename("new_code.py","code.py")
        os.rename("new_boot.py","boot.py")

        print(os.listdir())
        print(os.listdir("src"))
        print('Update installed, please reboot now')


    def _rmtree(self, directory):
        for entry in os.listdir(directory):
            print("removing:",entry)
            stats = os.stat(directory + "/" + entry)
            is_dir = stats[0] & 0x4000
            if is_dir:
                self._rmtree(directory + '/' + entry)
            else:
                os.remove(directory + '/' + entry)
        os.rmdir(directory)


    def _os_supports_rename(self) -> bool:
        self._mk_dirs('otaUpdater/osRenameTest')
        os.rename('otaUpdater', 'otaUpdated')
        result = len(os.listdir('otaUpdated')) > 0
        self._rmtree('otaUpdated')
        print("OS SUPPORTS RENAMING: ",result)
        return result


    def _copy_directory(self, fromPath, toPath):
        if not self._exists_dir(toPath):
            self._mk_dirs(toPath)

        for entry in os.ilistdir(fromPath):
            stats = os.stat(fromPath + "/" + entry)
            is_dir = stats[0] & 0x4000
            if is_dir:
                self._copy_directory(fromPath + '/' + entry, toPath + '/' + entry)
            else:
                self._copy_file(fromPath + '/' + entry, toPath + '/' + entry)


    def _copy_file(self, fromPath, toPath):
        with open(fromPath) as fromFile:
            with open(toPath, 'w') as toFile:
                CHUNK_SIZE = 512 # bytes
                data = fromFile.read(CHUNK_SIZE)
                while data:
                    toFile.write(data)
                    data = fromFile.read(CHUNK_SIZE)
            toFile.close()
        fromFile.close()


    def _exists_dir(self, path) -> bool:
        try:
            os.listdir(path)
            print(os.listdir(path))
            return True
        except:
            return False


    def _mk_dirs(self, path:str):
        paths = path.split('/')

        pathToCreate = ''
        for x in paths:
            self.mkdir(pathToCreate + x)
            pathToCreate = pathToCreate + x + '/'


    # different micropython versions act differently when directory already exists
    def mkdir(self, path:str):
        try:
            os.mkdir(path)
        except OSError as exc:
            if exc.args[0] == 17: 
                pass



    def modulepath(self, path):
        print("Module path called: adding ", self.module, "with",path)
        return self.module + '/' + path if self.module else path
