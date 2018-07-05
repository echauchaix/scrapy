import scrapy
import re
import lengow.config
from scrapy.loader import ItemLoader
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from scrapy.http import HtmlResponse

class LengowSpider(scrapy.Spider):
    name = 'lengow'
    allowed_domains = ['solution.lengow.com']
    start_urls = [
        'https://solution.lengow.com/'
    ]

    #login
    def parse(self, response):
        return scrapy.FormRequest.from_response(
            response,
            formdata={"login": lengow.config.login_lengow, 'password': lengow.config.password_lengow},
            callback=self.after_login
        )

    #display all the groups
    def after_login(self, response):
        url = 'https://solution.lengow.com/switch/?value=0'
        yield scrapy.Request(url=url,
                callback=self.go_to_listflow_page, dont_filter=True)

    #go to the marketplace page
    #url parameters goNumber take the number of items to display (set to 200 will display the whole flow list)
    def go_to_listflow_page(self, response):
        url = 'https://solution.lengow.com/marketplace/?type=marketplace&goNumber=200'
        yield scrapy.Request(url=url,
                callback=self.parse_flowlist_page)

    #parse the marketplace page to get all the urls for the active flows
    def parse_flowlist_page(self, response):
        urls = list()
        for flow in response.css('div.item'):
            #a flow is active when the image is "apply_f2.png"
            if '/view/images/apply_f2.png' in flow.css('div.logo img').xpath('@src').extract():
                flownumbers = flow.css('div.logo span::text').extract()
                for flownumber in flownumbers:
                    flownumber = self.regex_url(flownumber)
                    urlflow = 'https://solution.lengow.com/marketplace/flux' + str(flownumber) + '/gestion/?typePage=logs'
                    urls.append(urlflow)
        for url in urls:
            yield scrapy.Request(url=url,
               callback=self.parse_flow_page)

    #parse the flow log page to get the last 10 import of the product catalog date and ip
    def parse_flow_page(self, response):
        flowname = response.css('div.infosflux .title::text').extract()
        for i in range(2,12):
            selectordate = '.divNews > table > tr:nth-child(' + str(i) + ') > td:nth-child(1)::text'
            selectorip = '.divNews > table > tr:nth-child(' + str(i) + ') > td:nth-child(3)::text'
            position = i - 1
            if response.css(selectorip).extract_first() != '0':
                yield {
                    'flowname': flowname,
                    'flownum': self.regex_url(response.url),
                    'logdate' + str(position): response.css(selectordate).extract_first(),
                    'logip' + str(position): response.css(selectorip).extract_first(),
                }

    #regex which takes the url and returns the flow id 
    def regex_url(self, url):
        regex = r"\d+"
        return re.findall(regex, url)[0]
