from binascii import hexlify, unhexlify
import copy

from Crypto.Cipher import AES


class TransURL:
    def __init__(self, inst_hostname):
        self.inst_hostname = inst_hostname
        self.KEY_ = b'wrdvpnisthebest!'
        self.IV_ = b'wrdvpnisthebest!'
        self.size = 128

        self.URL_INFO = {
            'webvpn': {
                'protocol': 'https',
                'hostname': '',
                'port': '',
            },
            'target': {
                'protocol': '',
                'hostname': '',
                'port': '',
                'url': '/',
            }
        }

    def __encrypt(self, text):
        key = self.KEY_
        cfb_iv = self.IV_
        size = self.size
        cfb_cipher_encrypt = AES.new(key, AES.MODE_CFB, cfb_iv, segment_size=size)

        message = text.encode('utf-8')
        mid = cfb_cipher_encrypt.encrypt(message)
        res = hexlify(cfb_iv).decode('utf-8') + hexlify(mid).decode()

        return res

    def __get_url(self, url_info):
        hostname_target = url_info['target']['hostname']
        if hostname_target != '':
            hostname_encrypted_target = self.__encrypt(hostname_target)
        else:
            return ''

        port_webvpn = str(url_info['webvpn']['port'])
        if port_webvpn != '':
            port_webvpn = ':' + port_webvpn

        port_target = str(url_info['target']['port'])
        if port_target != '':
            port_target = '-' + port_target

        url = '%s://%s%s/%s%s/%s%s' % (
            url_info['webvpn']['protocol'],
            url_info['webvpn']['hostname'],
            port_webvpn,
            url_info['target']['protocol'],
            port_target,
            hostname_encrypted_target,
            url_info['target']['url'],
        )
        return url

    def __get_url_info(self, url, inst_hostname):
        url_info = copy.deepcopy(self.URL_INFO)

        url_info['webvpn']['hostname'] = inst_hostname

        st1 = url.split('://')
        url_info['target']['protocol'] = st1[0]
        if st1[0] == 'ws' or st1[0] == 'wss':
            url_info['webvpn']['protocol'] = 'wss'
        index = st1[1].find('/')
        if index == -1:
            st2 = st1[1][0:]
            url_info['target']['url'] = ''
        else:
            st2 = st1[1][0:index]
            url_info['target']['url'] = st1[1][index:]

        if st2.find(':') != -1:
            st3 = st2.split(':')
            url_info['target']['hostname'] = st3[0]
            url_info['target']['port'] = st3[1]
        else:
            url_info['target']['hostname'] = st2

        return url_info

    def __get_plain_text(self, ciphertext):
        key = self.KEY_
        cfb_iv = self.IV_
        size = self.size

        message = unhexlify(ciphertext.encode('utf-8'))
        cfb_cipher_decrypt = AES.new(key, AES.MODE_CFB, cfb_iv, segment_size=size)
        cfb_msg_decrypt = cfb_cipher_decrypt.decrypt(message).decode('utf-8')

        return cfb_msg_decrypt

    def url_encode(self, url):
        return self.__get_url(self.__get_url_info(url, self.inst_hostname))

    def url_decode(self, url):
        parts = url.split('/')
        pro = parts[3]
        key_cph = parts[4]

        if key_cph[:16] == hexlify(self.IV_).decode('utf-8'):
            print(key_cph[:32])
            return None
        else:
            hostname = self.__get_plain_text(key_cph[32:])
            fold = '/'.join(parts[5:])

            if "-" in pro:
                protocol, port = pro.split("-")
                return protocol + "://" + hostname + ":" + port + "/" + fold
            else:
                return pro + "://" + hostname + "/" + fold


if __name__ == '__main__':
    d = TransURL("webvpn.cpu.edu.cn")
    print(d.url_encode("ws://1.1.1.1:8800"))
    print(d.url_decode(d.url_encode("ws://1.1.1.1:8800")))
