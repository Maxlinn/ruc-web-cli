import argparse
import logging
import json
from functions import login, logout


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.description = f'Either call`python main.py --username YOUR_USERNAME --password YOUR_PASSWORD`' \
                         f'or `python.main.py --secrets SECRETS_JSON_FILENAME`' \
                         f'or `python.main.py`, which will use local `secrets.json` to login.'
    parser.add_argument('--secrets', '-s',
                        type=str,
                        default='secrets.json',
                        help='Secrets to login, '
                             'should be a json file with `username` and `password` inside, values are string.')
    parser.add_argument('--username', '-u',
                        type=str,
                        help='Username to login, typically your student id.')
    parser.add_argument('--password', '-p',
                        type=str,
                        help='Password to login, typically your password for https://v.ruc.edu.cn')
    parser.add_argument('--login',
                        action='store_true',
                        default=True,
                        help='Switch to do login, by default True.')
    parser.add_argument('--logout',
                        action='store_true',
                        help='Switch to do logout.')

    args = parser.parse_args()

    logger.info(f'args: {args}')

    if args.username is not None and args.password is not None:
        logger.info('reading username and password from command line arguments')
        username, password = args.username, args.password
    else:
        logger.info(f'reading username and password from json "{args.secrets}".')
        with open(args.secrets, 'r', encoding='utf-8') as f:
            j = json.load(f)
        username, password = str(j['username']), str(j['password'])

    logger.debug(f'received username = {username} and password = {password}')

    if args.logout:
        logout(username)
    elif args.login:
        login(username, password)


if __name__ == '__main__':
    main()