#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# enable debugging
import cgitb
cgitb.enable()

# import main web lib
import cgi

# set mime type
print "Content-Type: text/html;charset=utf-8\n"

# load the price API
import priceapi


# define the main functions and templates


def translate(text):
    # use any translation system you would like here
    return text


def getFavicon():
    # change here to adapt to your own website
    return '        <link rel="shortcut icon" href="favicon.ico">'
    

def getStylesheet():
    # change here to adapt to your own website
    return '        <link type="text/css" href="stylesheet.css" rel="stylesheet">'


def getContentsSource():
    result = ''
    for s in priceapi.sources:
        l = " ".join([s.Name,s.City+",",s.Country,str(s.Month)+"/"+str(s.Year)])
        if result:
            result += '\n'
        result += '    <div class="webprice-source-item">'+l+'</div>'
    return result


def getContentsSourcesSelect():
    result = '                <option value="All">'+translate("All")+'</option>'
    for s in priceapi.sources:
        result += '\n                <option value="'+s.Name+'">'+s.Name+'</option>'
    return result


def getContentsResults(terms,location,source):
    searchresults = priceapi.search(terms,location,source)
    result = ''
    if searchresults:
        result += '    <table class="webprice-results-table">\n'
        for res1 in searchresults:
            for res2 in res1[1]:
                result += '        <tr class="webprice-result-item">\n'
                result += '            <td class="webprice-result-source">'+res1[0].Name+'</td>\n'
                result += '            <td class="webprice-result-code">'+res2[0]+'</td>\n'
                result += '            <td class="webprice-result-text">'+res2[1]+'</td>\n'
                result += '            <td class="webprice-result-price">'+res2[2]+'</td>\n'
                result += '            <td class="webprice-result-unit">'+res2[3]+'</td>\n'
                result += '        </tr>\n'
        result += '    </table>'
    return result


htmltemplate = """<html>
    <head>
        <meta http-equiv="content-type" content="text/html; charset=UTF-8">
        <title>"""+translate("Price search")+"""</title>
        <meta content="Yorik van Havre" name="author">
%favicon%
%stylesheet%
    </head>

    <body>
%contents%
    </body>
</html>
"""


contentstemplate = """
<h2>"""+translate("Price search")+"""</h2>

<div class="webprice-sources">
%contents-sources%
</div>

<form id="priceapi" action="webprice.py" class="webprice-form" method="POST">
    <fieldset>
        <legend>"""+translate("Separate search term by a space to retrieve only entries that contain all the search terms. Use a | character to separate alternative search term (entries containing one OR the other will be retrieved).")+"""</legend>
        <div>
            <label for="webprice-terms">"""+translate("Search terms")+"""</label>
            <input name="webprice-terms" type="text" required autofocus>
            <label for="webprice-location">"""+translate("Location")+"""</label>
            <input name="webprice-location" type="text">
            <label for="webprice-sources-select">"""+translate("Sources")+"""</label>
            <select id="webprice-sources-select">
%contents-sources-select%
            </select>
            <input type="submit">
        </div>
    </fieldset>
</form>

<h3>"""+translate("Results")+"""</h3>

<div class="webprice-results">
%contents-results%
</div>
"""


# build the HTML output


contentsresults = ''
data = cgi.FieldStorage()
if data.length > 0:
    contentsresults += "got data\n"
    if data.has_key('webprice-terms'):
        contentsresults += "got terms\n"
        terms = data['webprice-terms'].value
        location = None
        if data.has_key('webprice-location'):
            if data['webprice-location']:
                location = data['webprice-location'].value
        source = None
        if data.has_key('webprice-sources-select'):
            if data['webprice-sources-select']:
                if data['webprice-sources-select'] != 'All':
                    source = data['webprice-sources-select'].value
        contentsresults = getContentsResults(terms,location,source)

contents = contentstemplate.replace("%contents-sources%",getContentsSource())
contents = contents.replace("%contents-sources-select%",getContentsSourcesSelect())
contents = contents.replace("%contents-results%",contentsresults)

# tabulate
contents = "\n".join(["        "+l for l in contents.split("\n")])

# build html
page = htmltemplate.replace("%favicon%",getFavicon())
page = page.replace("%stylesheet%",getStylesheet())
page = page.replace("%contents%",contents)
print page
    
