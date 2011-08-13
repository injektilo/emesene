# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import re

################################################################################
# WARNING: This stuff is unused, unless you plan to write a better parser
# you should jump to the used code somewhere down here.
################################################################################
from e3.common.XmlParser import DictObj

import gui

COLOR_MAP = (
    'ffffff','000000','00007F','009300','FF0000','7F0000','9C009C','FC7F00',
    'FFFF00','00FC00','009393','00FFFF','0000FC','FF00FF','7F7F7F','D2D2D2',
    'E7E6E4','CFCDD0','FFDEA4','FFAEB9','FFA8FF','B4B4FC','BAFBE5','C1FFA3',
    'FAFDA2','B6B4B7','A2A0A1','F9C152','FF6D66','FF62FF','6C6CFF','68FFC3',
    '8EFF67','F9FF57','858482','6E6D7B','FFA01E','F92611','FF20FF','202BFF',
    '1EFFA5','60F913','FFF813','5E6464','4B494C','D98812','EB0505','DE00DE',
    '0000D3','03CC88','59D80D','D4C804','333335','18171C','944E00','9B0008',
    '980299','01038C','01885F','389600','9A9E15','473400','4D0000','5F0162',
    '000047','06502F','1C5300','544D05')

TAG_DICT = {
    'a': 'background',
    'c': 'foreground',
    'b': ('weight', 'bold'),
    'u': ('underline', 'single'),
    'i': ('style', 'italic'),
    's': ('strikethrough', 'true'),
    '$': 'foreground',
    '#': ('weight', 'bold'),
    '@': ('underline', 'single'),
    '&amp;': ('style', 'italic'),
    '\'': ('strikethrough', 'true')
}

COLOR_TAGS = ('a', 'c', '$')

open_tag_re = re.compile('''(.*?)\[(/?)(\w+)(\=(\#?[0-9a-fA-F]+|\w+))?\]''',
                         re.IGNORECASE | re.DOTALL)
open_tag_old_re = re.compile('(.*?)\xb7(\$|#|(&amp;)|\'|@)((\#?[0-9a-fA-F]{6}|\d{1,2})?),?((\#?[0-9a-fA-F]{6}|\d{1,2})?)',
                         re.IGNORECASE | re.DOTALL)
close_tag_old_re = re.compile('(.*?)\xb7(0)', re.IGNORECASE | re.DOTALL)
#TODO: I think the other 'InGradient' regexes from the old parser have to be used too
special_character_re = re.compile('(&[a-zA-Z]+\d{0,3};|\%.)')

#regex used to remove plus markup
tag_plus_strip_re = re.compile('(\[\w(\=#?[0-9A-Fa-f]+|\=\w+)?\])|(\[\/\w+(\=#?[0-9A-Fa-f]+|\=\w+)?\])')
tag_plus_old_strip_re = re.compile('\·(\&|\@|\#|0)|\·\$(\d+|\#\w+)?(\,(\d+|\#\w+))?')

def parse_emotes(markup):
    '''search for emotes on markup and return a list of items with chunks of
    test and Emote instances'''
    accum = []
    for is_emote, text in gui.theme.emote_theme.split_smilies(markup):
        if is_emote:
            accum.append(
                {'tag': 'img',
                 'src': gui.theme.emote_theme.emote_to_path(text, True),
                 'alt': text, 'childs': []})
        else:
            accum.append(text)

    return accum

def _msnplus_to_dict(msnplus, message_stack, do_parse_emotes=True,
                     was_double_color=False):
    '''convert it into a dict, as the one used by XmlParser'''
    #STATUS: seems to work! (with gradients too)
    match = open_tag_re.match(msnplus)
    match_old = open_tag_old_re.match(msnplus)
    match_close_old = close_tag_old_re.match(msnplus)

    if not match and not match_old and not match_close_old: #only text
        if do_parse_emotes:
            parsed_markup = parse_emotes(msnplus)
        else:
            parsed_markup = [msnplus]

        message_stack.append(msnplus)
        return {'tag': 'span', 'childs': parsed_markup}
    if match and match_old:
        if len(match.group(1)) > len(match_old.group(1)):
            match = None
        else:
            match_old = None
    if match and match_close_old:
        if len(match.group(1)) > len(match_close_old.group(1)):
            match = None
        else:
            match_close_old = None
    if match_old and match_close_old:
        if len(match_old.group(1)) > len(match_close_old.group(1)):
            match_old = None
        else:
            match_close_old = None

    is_double_color = False
    is_background = False

    if match:
        entire_match_len = len(match.group(0))
        text_before = match.group(1)
        open_ = match.group(2) == '' #and not '/'
        tag = match.group(3)
        tag = tag.lower()
        arg = match.group(5)
    elif match_old:
        text_before = match_old.group(1)
        open_ = True
        tag = match_old.group(2)
        arg = match_old.group(4)
        arg2 = match_old.group(6)
        is_double_color = arg2 and arg and not was_double_color
        if is_double_color:
            entire_match_len = 0
        else:
            if not arg and arg2:
                is_background = True
            entire_match_len = len(match_old.group(0))
    elif match_close_old:
        entire_match_len = len(match_close_old.group(0))
        text_before = match_close_old.group(1)
        open_ = False
        tag = match_close_old.group(2)
        arg = ''

    if open_:
        if text_before.strip(' ') and not was_double_color: #just to avoid useless items (we could put it anyway, if we like)
            message_stack[-1]['childs'].append(text_before)
        if was_double_color or is_background:
            msgdict = {'tag': 'a', 'a': arg2, 'childs': []}
        else:
            msgdict = {'tag': tag, tag: arg, 'childs': []}
        message_stack.append(msgdict)
    else: #closing tags
        if arg:
            start_tag = message_stack[-1][tag]
            message_stack[-1][tag] = (start_tag, arg)
        if text_before.strip(' '): #just to avoid useless items (we could put it anyway, if we like)
            if do_parse_emotes:
                text_before = parse_emotes(text_before)
                message_stack[-1]['childs'] += text_before
            else:
                message_stack[-1]['childs'].append(text_before)
        tag_we_re_closing = message_stack.pop() #-1
        if type(message_stack[-1]) == dict:
            message_stack[-1]['childs'].append(tag_we_re_closing)
        else:
            message_stack.append(tag_we_re_closing)

    #go recursive!
    _msnplus_to_dict(msnplus[entire_match_len:], message_stack,
                     do_parse_emotes, is_double_color)

    return {'tag': 'span', 'childs': message_stack}

def _nchars_dict(msgdict):
    '''count how many character are there'''
    nchars = 0
    for child in msgdict['childs']:
        if type(child) in (str, unicode):
            nchars += len(special_character_re.sub('a', child))
        else:
            nchars += _nchars_dict(child)

    return nchars

def _color_gradient(color1, color2, length):
    '''returns a list of colors. Its length is length'''

    def dec2hex(n):
        """return the hexadecimal string representation of integer n"""
        if n < 16:
            return '0' + "%X" % n
        else:
            return "%X" % n

    def hex2dec(s):
        """return the integer value of a hexadecimal string s"""
        return int('0x' + s, 16)

    def full_hex2dec(colorstring):
        """return a tuple containing the integer values of the rgb colors"""
        hex3tohex6 = lambda col: col[0] * 2 + col[1] * 2 + col[2] * 2

        colorstring = colorstring.strip()

        if colorstring.startswith('#'):
            colorstring = colorstring[1:]

        if len(colorstring) == 3:
            colorstring = hex3tohex6(colorstring)

        r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
        r, g, b = [hex2dec(i.upper()) for i in (r, g, b)]
        return (r, g, b)

    rgb_tuple1 = full_hex2dec(color1)
    rgb_tuple2 = full_hex2dec(color2)

    colors = [''] * length
    for color_part in zip(rgb_tuple1, rgb_tuple2):
        step = (color_part[1] - color_part[0]) / (length - 1.0)
        for i in range(length - 1):
            colors[i] += dec2hex(int(color_part[0] + step * i))
        colors[length - 1] += dec2hex(color_part[1])

    return colors

def _name_to_hex(name):
    return hexColorNameDict.get(name.lower(), name)

def _hex_colors(msgdict):
    '''convert colors to hex'''
    if msgdict['tag']:
        tag = msgdict['tag']

        if tag in COLOR_TAGS:
            param = msgdict[tag]

            if type(param) == tuple: #gradient
                param1, param2 = param

                if len(param1) <= 2: #is not already hex
                    msgdict[tag] = (COLOR_MAP[int(param1)], msgdict[tag][1])
                if len(param2) <= 2: #is not already hex
                    msgdict[tag] = (msgdict[tag][0], COLOR_MAP[int(param2)])
            else: #normal color
                if len(param) <= 2: #is not already hex
                    msgdict[tag] = COLOR_MAP[int(param)]
                elif param.startswith('#'):
                    msgdict[tag] = param[1:]
                else:
                    #color from name
                    code = _name_to_hex(param)
                    msgdict[tag] = code[1:]

    for child in msgdict['childs']:
        if child and type(child) not in (str, unicode):
            _hex_colors(child)

def _gradientify_string(msg, attr, colors):
    '''apply sequence "colors" of colors (type attr) to msg'''
    result = {'tag': '', 'childs': []}

    split_msg = special_character_re.split(msg)

    for text in split_msg:
        if special_character_re.match(text):
            color = colors.pop(0)
            result['childs'].append({'tag': attr, attr: color,
                                     'childs': [text]})
            continue
        for char in text:
            color = colors.pop(0)
            result['childs'].append({'tag': attr, attr: color,
                                     'childs': [char]})

    return result

def _gradientify(msgdict, attr=None, colors=None):
    '''apply a gradient to that msgdict'''
    if not attr:
        attr = msgdict['tag']

    if colors is None:
        param_from, param_to = msgdict[attr]
        #param_from = COLOR_MAP[int(param_from)]
        #param_to = COLOR_MAP[int(param_to)]
        length = _nchars_dict(msgdict)
        if length != 1:
            colors = _color_gradient(param_from, param_to, length)
        msgdict['tag'] = ''
        del msgdict[attr]

    i = 0
    while colors and i < len(msgdict['childs']):
        this_child = msgdict['childs'][i]

        if type(this_child) in (str, unicode):
            msgdict['childs'][i] = _gradientify_string(this_child, attr, colors) #will consumate some items from colors!
        else:
            _gradientify(this_child, attr, colors)

        i += 1

def _dict_gradients(msgdict):
    '''apply gradients where needed'''
    if type(msgdict) != dict: return
    for subdict in msgdict['childs']:
        if type(subdict) == dict:
            tag = subdict['tag']
            if tag in subdict and type(subdict[tag]) == tuple:
                _gradientify(subdict)
            _dict_gradients(subdict)

def _dict_translate_tags(msgdict):
    '''translate 'a' to 'span' etc...'''
    #Work on this
    tag = msgdict['tag']
    if tag in TAG_DICT:
        msgdict['tag'] = 'span'
        if tag in COLOR_TAGS:
            msgdict[TAG_DICT[tag]] = '#%s' % msgdict[tag].upper()
        else:
            msgdict[TAG_DICT[tag][0]] = TAG_DICT[tag][1]
        del msgdict[tag]
    elif tag == 'img':
        pass
    elif tag not in ('span', ''):
        del msgdict[tag]
        msgdict['tag'] = ''
        msgdict['childs'].insert(0, '[%s]' % (tag, ))

    #Then go recursive!
    for child in msgdict['childs']:
        if type(child) == dict:
            _dict_translate_tags(child)

def msnplus(text, do_parse_emotes=True):
    '''given a string with msn+ formatting, give a DictObj
    representing its formatting.'''
    message_stack = [{'tag':'', 'childs':[]}]
    text = unicode(text, 'utf8') if type(text) is not unicode else text
    dictlike = _msnplus_to_dict(text, message_stack, do_parse_emotes)
    _hex_colors(dictlike)
    _dict_gradients(dictlike)
    _dict_translate_tags(dictlike)
    return DictObj(dictlike)

def msnplus_parse(nick):
    '''from a plus nick returns a pango markup'''
    dictlike = msnplus(nick, False)
    return dictlike.to_xml()

def _escape_special_chars(text):
    #escape special chars
    text = text.replace('\xc2\xb7&amp;', '\xc2\xb7&')
    text = text.replace('\xc2\xb7&quot;', '\xc2\xb7"')
    text = text.replace('\xc2\xb7&apos;', '\xc2\xb7\'')
    return text

def _deescape_special_chars(text):
    #unescape special chars
    text = text.replace('\xc2\xb7&', '\xc2\xb7&amp;')
    text = text.replace('\xc2\xb7"', '\xc2\xb7&quot;')
    text = text.replace('\xc2\xb7\'', '\xc2\xb7&apos;')
    return text

def msnplus_strip(text, useless_arg=None):
    '''
    given a string with msn+ formatting, give a string with same text but
    without MSN+ markup
    @param text The original string
    @param useless_arg This is actually useless, and is mantained just for
    compatibility with text
    '''

    text = _escape_special_chars(text)

    text = tag_plus_strip_re.sub('', text)
    text = tag_plus_old_strip_re.sub('', text)
    text = text.replace("no-more-color", '')

    text = _deescape_special_chars(text)

    return text

################################################################################
# WARNING: Good ol' emesene1 code from mohrtutchy, roger et. al.
# It might not be perfect or nice to see, but hell if it works, m3n.
################################################################################

colorCodesHexGradient = re.compile\
    ('\[[cC]=#([0-9A-Fa-f]{6})\](.*?)\[/[cC]=#([0-9A-Fa-f]{6}|#{6})\]')
backColorCodesHexGradient = re.compile\
    ('\[[aA]=#([0-9A-Fa-f]{6})\](.*?)\[/[aA]=#([0-9A-Fa-f]{6}|#{6})\]')

tagInGradient = r'(<span[^>]*>|</span>|'\
    '\[[aA]=[0-9]{1,2}\]|\[[aA]=#[0-9A-Fa-f]{6}\]|\[/[aA]=#{7}\]|'\
    '\[/[aA]=[0-9]{1,2}\]|\[/[aA]=#[0-9A-Fa-f]{6}\])'
specialInGradient = r'(&[a-zA-Z]+\d{0,3};|\%.)'
allInGradient = r'(<span[^>]*>|</span>|'\
    '\[[aA]=[0-9]{1,2}\]|\[[aA]=#[0-9A-Fa-f]{6}\]|\[/[aA]=#{7}\]|'\
    '\[/[aA]=[0-9]{1,2}\]|\[/[aA]=#[0-9A-Fa-f]{6}\]|&[a-zA-Z]+\d{0,3};|\%.)'

openName = r'(?<=\[[cC]=|\[[aA]=)[0-9a-zA-Z]{3,6}(?=\])'
closeName = r'(?<=\[/[cC]=|\[/[aA]=)[0-9a-zA-Z]{3,6}(?=\])'
openCode = r'(?<=\[[cC]=|\[[aA]=)[0-9]{1,2}(?=\])'
closeCode = r'(?<=\[/[cC]=|\[/[aA]=)[0-9]{1,2}(?=\])'

colorIrcCode = re.compile("\xb7\$([0-9]{1,2})?,?([0-9]{1,2})?")
colorIrcCodeFG = re.compile("(?<=\xb7\$)[0-9]{1,2}")
colorIrcCodeBG = re.compile("(?<=\xb7\$,)[0-9]{1,2}")
colorIrcCodeFGBG = re.compile("(?<=\xb7\$#[0-9a-fA-F]{6},)[0-9]{1,2}")
colorIrcHex = re.compile("\xb7\$(#[0-9a-fA-F]{6})?,?(#[0-9a-fA-F]{6})?")

#don't try to pack them into one regexp. please.

formatBb = {}
formatIrc = {}

tmpBb = "bius"
tmpIrc = "#&@'"

for i in range(4):
    bb = tmpBb[i]
    irc = tmpIrc[i]
    doubleCase = (bb+bb.upper(), bb+bb.upper())
    doubleIrc = (irc,irc)
    formatBb[bb] = re.compile('(\[[%s]\](.*?)\[/[%s]\])' % doubleCase)
    formatIrc[bb] = re.compile("\xb7(\%s)(.*?)(\xb7\%s|$)" % doubleIrc)
del bb, irc, doubleCase, doubleIrc

colorTags = re.compile('\[[cC]=#[0-9A-Fa-f]{6}\]|\[[cC]=[0-9]{1,2}\]|'\
    '\[/[cC]\]|\[/[cC]=[0-9]{1,2}\]|\[/[cC]=#[0-9A-Fa-f]{6}\]|'\
    '\[[cC]=[0-9A-Za-z]{1,6}\]|\[/[cC]=[0-9A-Za-z]{1,6}\]')
backColorTags = re.compile('\[[aA]=#[0-9A-Fa-f]{6}\]|\[[aA]=[0-9]{1,2}\]|'\
    '\[/[aA]\]|\[/[aA]=[0-9]{1,2}\]|\[/[aA]=#[0-9A-Fa-f]{6}\]|'\
    '\[[aA]=[0-9A-Za-z]{1,6}\]|\[/[aA]=[0-9A-Za-z]{1,6}\]')
colorIrcTags = re.compile('\xb7\$[0-9]{1,2},[0-9]{1,2}|'\
    '\xb7\$[0-9]{1,2}|\xb7\$,[0-9]{1,2}|\xb7\$#[a-fA-F0-9]{6},#[a-fA-F0-9]{6}|'\
    '\xb7\$#[a-fA-F0-9]{6}|\xb7\$,#[a-fA-F0-9]{6}')

getTagDict = {
    'background': ('background="#%s"'),
    'foreground': ('foreground="#%s"'),
    'b': ('weight="bold"'),
    'u': ('underline="single"'),
    'i': ('style="italic"'),
    's': ('strikethrough="true"'),
}

# color dict used to retreive common color codes from their names
hexColorNameDict = {
    'white': ('#ffffff'),
    'black': ('#000000'),
    'marine': ('#00007F'),
    'white': ('#ffffff'),
    'green': ('#009300'),
    'red': ('#FF0000'),
    'brown': ('#7F0000'),
    'purple': ('#9C009C'),
    'orange': ('#FC7F00'),
    'yellow': ('#FFFF00'),
    'lime': ('#00FC00'),
    'teal': ('#009393'),
    'aqua': ('#00FFFF'),
    'blue': ('#0000FC'),
    'pink': ('#FF00FF'),
    'gray': ('#7F7F7F'),
    'silver': ('#D2D2D2'),
    'mohr': ('#ff00de'),
    'c10ud': ('#696969')
}

class MsnPlusMarkupMohrtutchy:

    def replaceMarkup( self, text ):

        '''replace the [b][/b] etc markup for pango markup'''

        text = unicode(text,'utf8') if type(text) is not unicode else text
        text = _escape_special_chars(text)

        self.backgroundColor = self.frontColor = ''
                
        self.openSpan = None
        def q(dictionary, tag, text): #quick handler
            def handler(x):
                return self.getTag({tag: ''}, x.groups()[1])
            return re.sub(dictionary[tag], handler, text)

        text = re.sub('\xb70','',text)

        for tag in 'bius':
            text = q(formatBb, tag, text)
            text = q(formatIrc, tag, text)

        text = re.sub( openName, self.nameToHex, text)
        text = re.sub( closeName, self.nameToHex, text)
        text = re.sub( openCode, self.codeToHex, text)
        text = re.sub( closeCode, self.codeToHex, text)
        text = re.sub( colorIrcCodeFG, self.codeToHex, text)
        text = re.sub( colorIrcCodeBG, self.codeToHex, text)
        text = re.sub( colorIrcCodeFGBG, self.codeToHex, text)

        # I know these two lines are not very nice, I beg you pardon :P
        text = re.sub( '\[/[cC]\]', '[/c=#######]',text)
        text = re.sub( '\[/[aA]\]', '[/a=#######]',text)
        
        text = re.sub( colorCodesHexGradient, self.hexToTagGrad, text )
        text = re.sub( backColorCodesHexGradient, self.bHexToTagGrad, text )

        text = re.sub( '\[[cC]=#[0-9a-fA-F]{6}\]|'\
                '\[/[cC]=#[0-9a-fA-F]{6}\]|\[/c=#######\]','',text)
        text = re.sub( '\[[aA]=#[0-9a-fA-F]{6}\]|'\
                '\[/[aA]=#[0-9a-fA-F]{6}\]|\[/a=#######\]','',text)
        
        text = re.sub( colorIrcHex, self.ircHexToTag, text ) 

        if self.openSpan != None:
            #TODO: fix this with msgplus codes, '&#173;'?
            pos = text.find("no-more-color")
            if pos != -1:
                text = text.replace("no-more-color",'</span>')
            else:
                text += '</span>'

        return _deescape_special_chars(text)
        

    def codeToHex( self, data ):
        code=data.group()
        if int(code) < len(COLOR_MAP):
            hex = '#'+COLOR_MAP[int(code)].lower()
            return hex
        elif int(code) > 67 and int(code) < 100:
            return '#000000'
        else:
            return code

    def nameToHex( self, data ):
        code=data.group()
        return hexColorNameDict.get(code.lower(), code)
        
    def ircHexToTag( self, data ):
        text = ''
        color1, color2 = data.groups()
        try:
            color1 = color1[1:]
        except:
            pass
        try:
            color2 = color2[1:]
        except:
            pass

        if self.frontColor != '' and color1 == None:
            color1 = self.frontColor

        if self.backgroundColor != '' and  color2 == None:
            color2 = self.backgroundColor
        
        self.frontColor = color1
        self.backgroundColor = color2
        
        try:
            if color1 != None and color2 != None:
                fghex = color1.lower()
                bghex = color2.lower()
                text = self.getTag({'foreground': fghex, 'background': bghex},
                    None)

            elif color1 != None:
                fghex = color1.lower()
                text = self.getTag({'foreground': fghex}, None)
                        
            elif color2 != None:
                bghex = color2.lower()
                text = self.getTag({'background': bghex}, None)
        except IndexError:
            # i'm giving up. i can't deal with tuples. i fail
            pass
                    
        if self.openSpan != None:
            text = '</span>' + text

        if text:
            self.openSpan = True
            return text
        
    def dec2hex(self, n):
        """return the hexadecimal string representation of integer n"""
        if n<16:
            return '0' + "%X" % n
        else:
            return "%X" % n
     
    def hex2dec(self, s):
        """return the integer value of a hexadecimal string s"""
        return int('0x'+s, 16)

    def gradient(self, col1,col2,length):
        R1hex=col1[:2]
        G1hex=col1[2:4]
        B1hex=col1[4:6]
        R2hex=col2[:2]
        G2hex=col2[2:4]
        B2hex=col2[4:6]
        R1dec=self.hex2dec(R1hex.upper())
        G1dec=self.hex2dec(G1hex.upper())
        B1dec=self.hex2dec(B1hex.upper())
        R2dec=self.hex2dec(R2hex.upper())
        G2dec=self.hex2dec(G2hex.upper())
        B2dec=self.hex2dec(B2hex.upper())
        stepR =((float(R2dec)-float(R1dec))/(float(length)-float(1)))
        stepG =((float(G2dec)-float(G1dec))/(float(length)-float(1)))
        stepB =((float(B2dec)-float(B1dec))/(float(length)-float(1)))
        R = [0] * length 
        R[0]=self.dec2hex(R1dec)
        R[length-1]=self.dec2hex(R2dec)
        G = [0] * length 
        G[0]=self.dec2hex(G1dec)
        G[length-1]=self.dec2hex(G2dec)
        B = [0] * length 
        B[0]=self.dec2hex(B1dec)
        B[length-1]=self.dec2hex(B2dec)
        for i in range(1, length-1):
            R[i] = self.dec2hex(int(R1dec+stepR * i))
        for i in range(1, length-1):
            G[i] = self.dec2hex(int(G1dec+stepG * i))
        for i in range(1, length-1):
            B[i] = self.dec2hex(int(B1dec+stepB * i))
        colors = [0] * length
        for i in range(0,length):
           colors[i] = R[i] + G[i] + B[i]
        return colors

    def longTagged( self, colors, text):
        textSplit=filter(None,re.split(allInGradient,text))
        k=0
        for j in range(0,len(textSplit)):
            if len(re.findall(tagInGradient,textSplit[j])) == 0:
                tagged=''
                if len(re.findall(specialInGradient,textSplit[j])) == 0:
                    for i in range(0,len(textSplit[j])):
                        tagged=tagged + self.getTag\
                                ({'foreground': colors[k]},textSplit[j][i])
                        k=k+1
                else:
                    tagged=tagged + self.getTag\
                            ({'foreground': colors[k]},textSplit[j])
                    k=k+1
                textSplit[j]=tagged
        textn=''
        for j in range(0,len(textSplit)):
            textn=textn+textSplit[j]
        return textn

    def blongTagged( self, colors, text):
        textSplit=filter(None,re.split(allInGradient,text))
        k=0
        for j in range(0,len(textSplit)):
            if len(re.findall(tagInGradient,textSplit[j])) == 0:
                tagged=''
                if len(re.findall(specialInGradient,textSplit[j])) == 0:
                    for i in range(0,len(textSplit[j])):
                        tagged=tagged + self.getTag\
                                ({'background': colors[k]},textSplit[j][i])
                        k=k+1
                else:
                    tagged=tagged + self.getTag\
                            ({'background': colors[k]},textSplit[j])
                    k=k+1
                textSplit[j]=tagged
        textn=''
        for j in range(0,len(textSplit)):
            textn=textn+textSplit[j]
        return textn
  
    def hexToTagGrad( self, data ):
        color1 = data.group(1)
        text = data.group(2)
        text = re.sub(colorTags,'',text)
        text = re.sub(colorIrcTags,'',text)
        color2 = data.group(3)
        if color2 == '######' or color2 == color1:
            return self.getTag({'foreground': color1}, text)
        else:
            length = len(re.sub(specialInGradient,'a',\
                    re.sub(tagInGradient,'',text)))
            if length>1:
                colors=self.gradient(color1,color2,length)
                tagged = self.longTagged( colors, text)
                return tagged
            else:
                return text
    
    def bHexToTagGrad( self, data ):
        color1 = data.group(1)
        text = data.group(2)
        text = re.sub(backColorTags,'',text)
        text = re.sub(colorIrcTags,'',text)
        color2 = data.group(3)
        if color2 == '######' or color2 == color1:
            return self.getTag({'background': color1}, text)
        else:
            length = len(re.sub(specialInGradient,'a',\
                    re.sub(tagInGradient,'',text)))
            if length>1:
                colors=self.gradient(color1,color2,length)
                tagged = self.blongTagged( colors, text)
                return tagged
            else:
                return text
    
    def getTag( self, attrdict, text ):
        attrs = []
        for key in attrdict.keys():
            if key in getTagDict:
                attr = getTagDict[key]
            attr = attr.replace("%s", attrdict[key])
            attrs.append(attr)

        tagattr = ''
        for attr in attrs:
            tagattr += attr
        
        if text == None:
            return '<span ' + tagattr + '>'
        else:
            return '<span ' + tagattr + '>' + text + '</span>'

if __name__ == '__main__':
    nick = '''[a=#f0Ff00]foo[b]bar[/b] rulez, [i]ain't it?[/i][/A] we say'''
    nick = '''[M]Implement[i][!][]ing[/i] [c=2]MS[N][/c] [c=3]PLUS[/c]'''

    print 'NICK', nick

    dictlike = msnplus(nick)
    print 'DICT', dictlike
    print 'XML', dictlike.to_xml()


    import sys
    sys.path.append('../..')
    from gui.gtkui import RichBuffer
    import gtk

    window = gtk.Window()
    window.connect("delete-event", gtk.main_quit)
    textview = gtk.TextView()
    buff = RichBuffer.RichBuffer()
    textview.set_buffer(buff)
    #window.add(textview)
    #buff._put_formatted(DictObj(dictlike))
    buff.put_formatted(dictlike.to_xml())

    label = gtk.Label()
    label.set_markup(dictlike.to_xml())

    window.add(label)

    window.show_all()
    gtk.main()

