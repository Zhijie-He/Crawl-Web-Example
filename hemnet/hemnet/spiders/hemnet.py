# -*- coding: utf-8 -*-
# @Author: Zhijie
# @Date:   2021-04-23 22:30:52
# @Last Modified by:   lenovo
# @Last Modified time: 2021-04-24 11:25:29


# before we start coding, we will go to the website and analyze it
# hemnet.se
# scrapy tutorial : https://docs.scrapy.org/en/latest/
import scrapy
import time
# add these two library to let the spider do something when the proecess end
from pydispatch import dispatcher
from scrapy import signals
# save the data into json file
import json


class HemnetSpider(scrapy.Spider):
	# identifies the Spider. It must be unique within a project, that is, you can’t set the same name for different Spiders.
    name = "hemnet" # this specify the project name

    start_urls = ["https://www.hemnet.se/kommande/bostader?location_ids%5B%5D=17745&page=3"]

    count = 0
    results = {}

    # spider end step 1
    #
    def __init__(self):
    	dispatcher.connect(self.spider_closed, signals.spider_closed)

    def parse(self, response):
    	# as we have analyzed from the target website, the elements we want is the ul with the class of normal-results
		# if the ul have the id, we need use #, i.e., ul.#normal-results
    	# here if we just print response.css('ul.normal-results'), this is a object type that cannot help us
    	# so we need use get() function, i.e., response.css('ul.normal-results').get()

    	# so now we get the general information, but we still need to crop it because there are other things like ads in there
    	# we find the valuable infomation is in li tag with the unique class of normal-results__hit
    	# here if we want to select the children tag, we use >(arrow or greater than symbol)
    	
    	#for li_item in response.css('ul.normal-results > li.normal-results__hit'):
    		#print(li_item.get())

    	# here we get all the housing information, but next we need to find each link which will link to detailed pages
    	# here we want to get all the valuable link, remember to use sing quote inside and double quotes outside
    	#for li_item in response.css("ul.normal-results > li.normal-results__hit > a::attr('href')"):
    		#print(li_item.get())

    	# now if we want to find all the link, we can implement it with the next page button
    	#next_page = response.css("a.next_page::attr('href')")
    	#print(next_page.get())

    	#now we can get the next_page link via next page button, when the next page button is none meaning this is the final page
    	for li_item in response.css("ul.normal-results > li.normal-results__hit > a::attr('href')"):
    		yield scrapy.Request(url = li_item.get(), callback = self.parseInnerPage)
    		time.sleep(2) # give the server a wait time or else it will damage the server which will probably ban ur ip address


    	next_page = next_page = response.css("a.next_page::attr('href')").get()
    	if next_page is not None:
    		# here we know the next_page url is the relative of link, we can use follow meathod to concaten them automatically
    		# or else we can connect them manuually  
    		# recallback function is parse itself
    		next_page = response.urljoin(next_page)
    		time.sleep(1) 
    		yield scrapy.Request(url = next_page, callback = self.parse)
    def parseInnerPage(self, response):
    	# here we can use ::text to get the string content
    	street_name = response.css("h1.qa-property-heading::text").get()
    	price = response.css("p.property-info__price::text").get()
    	# but for price, if we get the price with above method without filtering, there are many spaces and kr(unit)
    	price = price.replace("kr","") # replace kr money unit with none
    	# Note, due to the white space in web is &nbsp; which is different from " " -> using u"\xa0"-> represent the &nbsp,which could get from google
    	# u stands for unicode
    	price = price.replace(u"\xa0","") 

    	attrDict = {}
    	# as we can analyse from the website html structure, all the valuable data is in this form
    	for attrs in response.css("div.property-attributes > div.property-attributes-table > dl.property-attributes-table__area > div.property-attributes-table__row"):
    		# get label
    		attrsLabel = attrs.css("dt::text").get()
    		# clean label
    		if attrsLabel is not None:
    			attrsLabel = attrsLabel.replace(u"\n","")
    			attrsLabel = attrsLabel.replace(u"\t","")
    			attrsLabel = attrsLabel.replace(u"\xa0","")
    			attrsLabel = attrsLabel.strip()

    		attrsValue = attrs.css("dd::text").get()
    		# clean attrsValue
    		if attrsValue is not None:
    			attrsValue = attrsValue.replace(u"\n","")
    			attrsValue = attrsValue.replace(u"\t","")
    			attrsValue = attrsValue.replace(u"\xa0","")
    			# remove some special str in the Value
    			attrsValue = attrsValue.replace("kr/mån","")
    			attrsValue = attrsValue.replace("kr/m²","")
    			attrsValue = attrsValue.replace("kr/år","")
    			attrsValue = attrsValue.replace("m²","")
    			attrsValue = attrsValue.replace("rum","")

    			attrsValue = attrsValue.strip()
    		# we find there is a label is None, we dont need it
    		if attrsLabel is not None:
    			attrDict[attrsLabel] = attrsValue

    	# save the dict to global data
    	# implement the increment using the self.count signal
    	self.results[self.count] = {
    		"streetName" : street_name,
    		"price": price,
    		"attrs": attrDict
    	}
    	self.count = self.count + 1

    # spider end step 2
    def spider_closed(self, spider):
    	# write the data to json file
    	with open('data.json', 'w') as fp:
    		json.dump(self.results, fp)