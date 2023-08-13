'''
### Parsing script for the PHUB package. ###
'''

from __future__ import annotations

import json
import js2py
from phub import consts
from phub.utils import log

from sys import getsizeof

from typing import TYPE_CHECKING
if TYPE_CHECKING: from classes import Video

def renew(video: Video) -> None:
    '''
    Attempt to renew the connection with Pornhub.
    
    Args:
        video (Video): The object that called the parser.
    '''
    
    # TODO - REFACTOR with regexes
    
    # Get script and cookie part
    log('parse', 'Attempting to renew connection')
    
    javascript = video.page.split('<!--')[1].split('//-->')[0]  
    script, cookies = javascript.split('document.cookie=')
    
    func = script[:-2] + 'return [n, p, s];}'
    n, p, s = js2py.eval_js(func)()
    
    # Build the cookie
    cookie_string = cookies.split(';\n')[0]
    end = cookie_string.split('s+":')[1].split(';path')[0]
    cookie = f'{n}*{p / n}:{s}:{end}'
    log('parse', 'Injecting calculated cookie:', cookie)
    
    # Send cookie and reload page
    video.client.session.cookies.set('RNKEY', cookie)
    video.refresh()

def resolve(video: Video) -> dict:
    '''
    Resolves obfuscation that protect PornHub video M3U files.
    
    Args:
        video (Video): The object that called the parser.
    
    Returns:
        dict: A dictionnary containing clean video data, fresh from PH.
    '''
    
    log('parse', 'Resolving page JS script...', level = 5)
    
    # TODO - REFACTOR
    
    try:
        flash, ctx = consts.regexes.video_flashvar(video.page)[0]
    
    except:
        # Invalid response, try to renew connection
        renew(video)
        
        print(video.client.session.cookies)
        
        try:
            flash, ctx = consts.regexes.video_flashvar(video.page)[0]
        
        except:
            raise consts.ParsingError()

    script = video.page.split("flashvars_['nextVideo'];")[1].split('var nextVideoPlay')[0]
    log('parse', 'Formating flash:', flash, level = 5)
    
    # Load context
    data: dict = json.loads(ctx)
    
    # Format the script
    script = ''.join(script.replace('var', '').split())
    script = consts.regexes.sub_js_comments('', script)
    script = script.replace(flash.replace('var', ''), 'data')
    
    # Execute the script
    exec(script) # In case you ask, what we are doing here is converting the obfuscated Pornhub JS code into python code so that we can execute it and directly get the video M3U file.
    log('parse', 'Execution successful, script resolved', level = 5)
    
    return data

# EOF