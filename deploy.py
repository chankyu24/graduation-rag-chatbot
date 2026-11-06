"""Cloud entrypoint for the same Streamlit app, with a provider-assigned port."""
import os
from pathlib import Path
import sys


def server_arguments():
    raw=os.getenv('PORT','8501')
    try: port=int(raw)
    except ValueError as exc: raise ValueError('PORT는 정수여야 합니다.') from exc
    if not 1<=port<=65535: raise ValueError('PORT는 1~65535 범위여야 합니다.')
    return ['streamlit','run',str(Path(__file__).with_name('app.py')),
            '--global.developmentMode=false','--server.address=0.0.0.0',
            f'--server.port={port}','--server.headless=true','--browser.gatherUsageStats=false']


if __name__=='__main__':
    from streamlit.web import cli
    sys.argv=server_arguments()
    sys.exit(cli.main())
