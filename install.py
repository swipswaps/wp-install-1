import sys
from random import choice
from string import ascii_lowercase, ascii_uppercase, digits
import pymysql.cursors
import requests
import zipfile

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

def logo():
    print("""
                    __      _____ ___         _        _ _ 
Author:  bmcculley  \ \    / / _ \_ _|_ _  __| |_ __ _| | |
Version: 0.1         \ \/\/ /|  _/| || ' \(_-<  _/ _` | | |
License: BSD 3        \_/\_/ |_| |___|_||_/__/\__\__,_|_|_|
""")

def complete():
    print("""
                             
                     `......`                     
               `://///:----::////:`               
            ./+/. `-:/+oooo+/:-` ./++.            
          :o:``:oyhhhhhhhhhhhhhhyo:``:o:          
        :o- -ohhhhhhhhhhhhhhhhhhhhhh/` -o:        
      `o/ .shhhhhhhhhhhhhhhhhhhhhh+`     /o`      
     `s- `///:::shh/:://///:::yhhh.       .s`     
    `s. `    `syhhhhyo     .yyhhhhs`     : .s`    
    +/ :s     :hhhhhhh+     +hhhhhhs`    s/ :o    
   `y` yh/     ohhhhhhh-    `yhhhhhhy`  `yh` y`   
   :o -hhh.    `hhhhhhhh`    .hhhhhhh:  /hh: +:   
   /+ :hhhy`    :hhhhhhh-     +hhhhhh: .hhh/ //   
   :o -hhhho     ohhhhh+ -     yhhhhy``yhhh: +:   
   `y `yhhhh:    `hhhhy`/h.    .hhhh: +hhhh` y`   
    +/ :hhhhh.    :hhh-.hhy`    +hhs -hhhh/ :o    
    `s. +hhhhy     oh+ shhho     sh.`yhhho .s`    
     `s. /hhhh+    `s`+hhhhh:    .+ ohhh/ .s.     
      `o/ .shhh-     .hhhhhhh.     :hhs. :o`      
        :o- -ohh`   `yhhhhhhhy    `yo- -o:        
          :o:``:/   +hhhhhhhhh+   .``:o/          
            .++:.   /+oossoo+/-  .:++-            
               `:////:------:////:.               
                     `..--..`           
""")

def show_help():
    print("""
+-----------------------------------------------------------------------+
|             WPInstall General Usage and Information                   |
+-----------------------------------------------------------------------+
""")

def generate_random_username(length=8, chars=ascii_lowercase+digits):
    """ This function generates a random username.
    It defaults to a length of 8 characters.
    """
    return ''.join([choice(chars) for i in xrange(length)])

def gen_password(length=16, chars=ascii_lowercase+ascii_uppercase+digits):
    """ Generate a secure random password
    """
    chars = chars + "!@#$%^&*()"
    return ''.join([choice(chars) for i in xrange(length)])

# this function needs to accept more parameters
def create_database(db_host, db_admin, dba_pass, db_name, db_user, db_pass):
    # create the database connection
    conn = pymysql.connect(host=db_host,
                            user=db_admin,
                            password=dba_pass,
                            charset="utf8")

    try:
        with conn.cursor() as cursor:
            sql = "create database %s"% db_name
            cursor.execute(sql)
            sql = "create user '%s'@'localhost' identified by '%s'"% (db_user, db_pass)
            cursor.execute(sql)
            sql = "grant all privileges on %s . * to '%s'@'localhost'"% (db_name, db_user)
            cursor.execute(sql)
            sql = "flush privileges"
            cursor.execute(sql)

        conn.commit()
    finally:
        conn.close()

def download_unzip_wp(path_to_install):
    # download the latest wordpress and extract
    r = requests.get(wpdl, stream=True)
    z = zipfile.ZipFile(StringIO.StringIO(r.content))
    z.extractall(path=path_to_install)
    # we should check and set the permissions properly
    # looks like the best method would be using os stat
    # https://stackoverflow.com/a/16249655

def install_wp(site_url, site_name, site_user, site_pass, site_email):
    # use requests to install wp
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'})
    # let's build the first POST 
    url_setup = site_url + "/wp-admin/setup-config.php?step=2"
    post_data = {
                    'dbname':db_name,
                    'uname':db_user,
                    'pwd':db_pass,
                    'dbhost':db_host,
                    'prefix':db_prefix,
                    'language':'',
                    'submit':'Submit'
                }
    r = session.post(url_setup, data=post_data)
    # check to make sure this returned ok
    if r.status_code == requests.codes.ok:
        # oops, we need to get request this url too
        url_install_1 = site_url + "/wp-admin/install.php?language=en_US"
        r = session.get(url_install_1)
        if r.status_code == requests.codes.ok:
            url_install = site_url + "/wp-admin/install.php?step=2"
            post_data = {
                            'weblog_title':site_name,
                            'user_name':site_user,
                            'admin_password':site_pass,
                            'pass1-text':site_pass,
                            'admin_password2':site_pass,
                            'pw_weak':'on',
                            'admin_email':site_email,
                            'Submit':'Install+WordPress',
                            'language':site_lang
                        }
            r = session.post(url_install, data=post_data)
            if r.status_code == requests.codes.ok:
                return "WordPress successfully installed."
    return "oh snap, something went wrong."

if __name__ == '__main__':
    logo()

    if len(sys.argv) > 1:
        print("setting configuration options")
        
        config = configparser.ConfigParser()
        config.read('config.ini')

        if 'site_settings' not in config or \
            'site_details' not in config or \
            'database_settings' not in config:
            print("Does the config file exist and have all the correct sections?")
            sys.exit()

        # site_settings
        site_url = config['site_settings']['site_url']
        path_to_install = config['site_settings']['path_to_install']
        wpdl = config['site_settings']['wpdl']

        # site_details
        site_name = config['site_details']['site_name']
        site_user = config['site_details']['site_user']
        site_pass = config['site_details']['site_pass']
        confirm_pass = config['site_details']['confirm_pass']
        site_email = config['site_details']['site_email']
        se_vis = config['site_details']['se_vis']
        site_lang = config['site_details']['site_lang']

        # database_settings
        db_host = config['database_settings']['db_host'] 
        db_admin = config['database_settings']['db_admin']
        dba_pass = config['database_settings']['dba_pass']
        db_name = config['database_settings']['db_name']
        db_user = config['database_settings']['db_user']
        db_pass = config['database_settings']['db_pass']
        db_prefix = config['database_settings']['db_prefix']

        print("creating the database")
        create_database(db_host, db_admin, dba_pass, db_name, db_user, db_pass)
        print("done")
        print("downloading wordpress to the install directory")
        download_unzip_wp(path_to_install)
        print("all set")
        print("let's install WordPress")
        print(install_wp(site_url, site_name, site_user, site_pass, site_email))
    else:
        show_help()