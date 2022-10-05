import argparse
import logging
import json
import time
import impl


def main():
    global logger

    parser = argparse.ArgumentParser()
    parser.description = f'Either call`python main.py --username YOUR_USERNAME --password YOUR_PASSWORD`' \
                         f'or `python.main.py --secrets SECRETS_JSON_FILENAME`' \
                         f'or `python.main.py`, which will use local `secrets.json` to login.'
    parser.add_argument('--username', '-u',
                        type=str,
                        help='Username to login, typically your student id.')
    parser.add_argument('--password', '-p',
                        type=str,
                        help='Password to login.')
    parser.add_argument('--secrets', '-s',
                        type=str,
                        default='secrets.json',
                        help='Secrets to login, '
                             'should be a json file with `username` and `password` inside, values are string.')
    parser.add_argument('--login',
                        action='store_true',
                        default=True,
                        help='Whether to do login, by default true.')
    parser.add_argument('--logout',
                        action='store_true',
                        help='Whether to do logout, has higher priority than `--login`.')
    parser.add_argument('--portal',
                        type=str,
                        default='https://go.ruc.edu.cn',
                        help='Portal of your school, for RUC, it is https://go.ruc.edu.cn.')
    parser.add_argument('--delay',
                        type=int,
                        default=0,
                        help='Login or logout after certain seconds, '
                             'come in handy when waiting for the device connecting to ap.')

    args = parser.parse_args()

    # if `--logout` is true, `--login` will not work.
    if args.logout:
        args.login = False

    logger.info(f'args: {args}')

    # both username and password are not None
    if all((args.username, args.password)):
        logger.info('reading username and password from command line arguments.')
        username, password = args.username, args.password
    else:
        logger.info(f'reading username and password from json "{args.secrets}".')
        with open(args.secrets, 'r', encoding='utf-8') as f:
            j = json.load(f)
        username, password = str(j['username']), str(j['password'])
    logger.debug(f'received username = {username} and password = {password}')

    if args.delay:
        logger.info(f'going to sleep for {args.delay} seconds...')
        time.sleep(args.delay)
        logger.info(f'awake.')

    impl.set_portal_base_url(args.portal)
    if args.login:
        impl.login(username, password)
    elif args.logout:
        impl.logout(username)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    main()