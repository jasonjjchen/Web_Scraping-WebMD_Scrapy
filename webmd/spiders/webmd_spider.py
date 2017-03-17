from scrapy import Spider, Request
from scrapy.selector import Selector
from webmd.items import WebmdItem
import urllib
import re

headers = {'User-Agent': 'Chrome/56.0.2924.87', 'enc_data': 'OXYIMo2UzzqFUzYszFv4lWP6aDP0r+h4AOC2fYVQIl8=', 'timestamp': 'Thu, 09 Feb 2017 02:11:34 GMT', 'client_id': '3454df96-c7a5-47bb-a74e-890fb3c30a0d'}

class WebmdSpider(Spider):
    name = "webmd_spider"
    allowed_urls = ['http://www.webmd.com/']
    start_urls = ['http://www.webmd.com/drugs/index-drugs.aspx?show=conditions']


    def parse(self, response):
        # follow links to next alphabet page
        atoz = response.xpath('//*[@id="drugs_view"]/li/a/@href').extract()
        print "parsing..."
        for i in range(2, len(atoz)):

            yield Request(response.urljoin(atoz[i]), \
                                 callback = self.parse_az,\
                          dont_filter= True)


    def parse_az(self, response):
        # follow links to condition
        Aa = response.xpath('//*[@id="showAsubNav"]/ul/li').extract()
        print "selecting alphabet..."
        for i in range(len(Aa)):

            yield Request(response.urljoin(response.xpath('//*[@id="showAsubNav"]/ul/li//a/@href').extract()[i]), \
                          callback = self.parse_condition,\
                          dont_filter= True)


    def parse_condition(self, response):
        # follow links to drugs
        table = response.xpath('//*[@id="az-box"]/div//a').extract()
        print "scraping condition and following link to drugs..."
        for i in range(len(table)):
            Condition = response.xpath('//*[@id="az-box"]/div//a/text()').extract()[i]

            yield Request(response.urljoin(response.xpath('//*[@id="az-box"]/div//a/@href').extract()[i]), \
                          callback = self.parse_drug, meta = {'Condition' : Condition},\
                          dont_filter= True)


    def parse_drug(self, response):
        # following links to drug details
        Condition = response.meta['Condition']

        print "scraping drug info and following link to details..."

        if re.search('Please select a condition below to view a list', response.body):
            yield Request(response.urljoin(response.xpath('//*[@id="fdbSearchResults"]/ul/li[1]/a//@href').extract()[0]),\
                          callback = self.parse_drug, meta = {'Condition': Condition},\
                          dont_filter= True)

        else:

            rows = response.xpath('//*[@id="vit_drugsContent"]/div/div/table[2]/tr').extract()

            for i in range(len(rows)):
                Drug = response.xpath('//*[@id="vit_drugsContent"]/div/div/table[2]/tr/td[1]/a/text()').extract()[i]
                Indication = response.xpath('//*[@id="vit_drugsContent"]/div/div/table[2]/tr/td[2]/@class').extract()[i].replace('drug_ind_fmt', '')
                Type = response.xpath('//*[@id="vit_drugsContent"]/div/div/table[2]/tr/td[3]/@class').extract()[i].replace('drug_type_fmt', '')
                Review = response.xpath('//*[@id="vit_drugsContent"]/div/div/table[2]/tr/td[4]/a/text()').extract()[i].replace('\r\n', '')

                aspx_index = response.xpath('//*[@id="vit_drugsContent"]/div/div/table[2]/tr/td[1]/a/@href').extract()[i].find('aspx') + 4

                yield Request(response.urljoin(response.xpath('//*[@id="vit_drugsContent"]/div/div/table[2]/tr/td[1]/a//@href').extract()[i][:aspx_index]),\
                              callback = self.parse_details, meta = {'Condition': Condition, 'Drug': Drug, 'Indication': Indication, 'Type': Type, 'Review': Review},\
                              dont_filter= True)


    def parse_details(self, response):
        Condition = response.meta['Condition']
        Drug = response.meta['Drug']
        Indication = response.meta['Indication']
        Type = response.meta['Type']
        Review = response.meta['Review']

        print "scraping details and following link to contraindications..."

        if re.search('The medication you searched for has more', response.body):
            yield Request(response.urljoin(response.xpath('//*[@id="ContentPane28"]/div/section/p[1]/a//@href').extract()[0]), \
                          callback = self.parse_details, meta = {'Condition': Condition, 'Drug': Drug, 'Indication': Indication, 'Type': Type, 'Review': Review},\
                          dont_filter= True)

        else:
            Use = ' '.join(response.xpath('//*[@id="ContentPane28"]/div/div/div/div[3]/div[1]/div[1]/h3/preceding-sibling::p//text()').extract())
            HowtoUse = ' '.join(response.xpath('//*[@id="ContentPane28"]/div/div/div/div[3]/div[1]/div[1]/h3/following-sibling::p//text()').extract())
            Sides = ' '.join(response.xpath('//*[@id="ContentPane28"]/div/div/div/div[3]/div[2]/div/p[1]//text()').extract()).replace('\r\n', '')
            Precautions = ' '.join(response.xpath('//*[@id="ContentPane28"]/div/div/div/div[3]/div[3]/div/p//text()').extract())
            Interactions = ' '.join(response.xpath('//*[@id="ContentPane28"]/div/div/div/div[3]/div[4]/div[1]/p[2]//text()').extract())
            revurl = response.xpath('//*[@id="ContentPane28"]/div/div/div/div[2]/nav/ul/li[7]/a//@href').extract()[0]

            if re.search('(rx/)(\d+)',response.xpath('//*[@id="ContentPane28"]/div/div/div/div[4]/div[1]/div/a/@href').extract()[0]):
                priceid = re.search('(rx/)(\d+)',response.xpath('//*[@id="ContentPane28"]/div/div/div/div[4]/div[1]/div/a/@href').extract()[0]).group(2)

            else:
                priceid = ''

            if not Use:
                Use = ' '
            if not Sides:
                Sides = ' '
            if not Interactions:
                Interactions = ' '
            if not Precautions:
                Precautions = ' '
            if not HowtoUse:
                HowtoUse = ' '

            if re.search('COMMON BRAND NAME', response.body):
                BrandName = ', '.join(response.xpath('//*[@id="ContentPane28"]/div/header/section/section[1]/p/a/text()').extract())
                GenName = response.xpath('//*[@id="ContentPane28"]/div/header/section/section[2]/p/text()').extract()[0]

                if not BrandName:
                    BrandName = ' '
                if not GenName:
                    GenName = ' '


            elif re.search('GENERIC NAME', response.body):
                BrandName = ' '
                GenName = response.xpath('//*[@id="ContentPane28"]/div/header/section/section[1]/p/text()').extract()[0]

                if not GenName:
                    GenName = ' '

            else:
                GenName = ' '
                BrandName = ' '


            yield Request(response.urljoin(response.url + '/list-contraindications'),\
                          callback = self.parse_avoid, meta = {'Condition': Condition, 'Drug': Drug, 'Indication': Indication, 'Type': Type, 'Review': Review,\
                                                               'Use': Use, \
                                                               'HowtoUse': HowtoUse, \
                                                               'Sides': Sides,\
                                                                'Precautions': Precautions,\
                                                               'Interactions': Interactions,\
                                                               'BrandName': BrandName,\
                                                               'GenName': GenName,\
                                                               'revurl': revurl,\
                                                               'priceid': priceid},\
                          dont_filter= True)


    def parse_avoid(self, response):
        Condition = response.meta['Condition']
        Drug = response.meta['Drug']
        Indication = response.meta['Indication']
        Type = response.meta['Type']
        Review = response.meta['Review']
        Use = response.meta['Use']
        HowtoUse = response.meta['HowtoUse']
        Sides = response.meta['Sides']
        Precautions = response.meta['Precautions']
        Interactions = response.meta['Interactions']
        BrandName = response.meta['BrandName']
        GenName = response.meta['GenName']
        revurl = response.meta['revurl']
        priceid = response.meta['priceid']

        print "scraping avoid use cases..."

        if re.search("We\'re sorry, but we couldn\'t find the page you tried", response.body):
            AvoidUse = ' '
            Allergies = ' '

        elif re.search('Conditions:', response.body):
            AvoidUse = ' '.join(response.xpath('//*[@id="ContentPane28"]/div/article/section/p[2]/text()').extract())
            Allergies = ' '.join(response.xpath('//*[@id="ContentPane28"]/div/article/section/p[3]/text()').extract())

        elif re.search('Allergies:', response.body):
            AvoidUse = ' '
            Allergies = ' '.join(response.xpath('//*[@id="ContentPane28"]/div/article/section/p[2]/text()').extract())

        else:
            AvoidUse = ' '
            Allergies = ' '

        if not AvoidUse:
            AvoidUse = ' '
        if not Allergies:
            Allergies = ' '

        yield Request(response.urljoin(revurl), \
                      callback=self.parse_reviews,
                      meta={'Condition': Condition, 'Drug': Drug, 'Indication': Indication, 'Type': Type,
                            'Review': Review, \
                            'Use': Use, \
                            'HowtoUse': HowtoUse, \
                            'Sides': Sides, \
                            'Precautions': Precautions, \
                            'Interactions': Interactions, \
                            'BrandName': BrandName, \
                            'GenName': GenName, \
                            'AvoidUse': AvoidUse,\
                            'Allergies': Allergies,\
                            'priceid': priceid}, \
                      dont_filter=True)


    def parse_reviews(self, response):
        Condition = response.meta['Condition']
        Drug = response.meta['Drug']
        Indication = response.meta['Indication']
        Type = response.meta['Type']
        Review = response.meta['Review']
        Use = response.meta['Use']
        HowtoUse = response.meta['HowtoUse']
        Sides = response.meta['Sides']
        Precautions = response.meta['Precautions']
        Interactions = response.meta['Interactions']
        BrandName = response.meta['BrandName']
        GenName = response.meta['GenName']
        AvoidUse = response.meta['AvoidUse']
        Allergies = response.meta['Allergies']
        priceid = response.meta['priceid']


        if re.search('Rate this treatment and share your opinion', response.body):

            Effectiveness = ' '
            EaseofUse = ' '
            Satisfaction = ' '

            yield Request('http://www.webmd.com/search/2/api/rx/forms/v2/' + priceid, \
                          method='GET', headers=headers, \
                          callback=self.parse_prices, \
                          meta={'Condition': Condition, 'Drug': Drug, 'Indication': Indication, 'Type': Type,
                                'Review': Review, \
                                'Use': Use, \
                                'HowtoUse': HowtoUse, \
                                'Sides': Sides, \
                                'Precautions': Precautions, \
                                'Interactions': Interactions, \
                                'BrandName': BrandName, \
                                'GenName': GenName, \
                                'AvoidUse': AvoidUse, \
                                'Allergies': Allergies,
                                'Effectiveness': Effectiveness, \
                                'EaseofUse': EaseofUse, \
                                'Satisfaction': Satisfaction}, \
                          dont_filter=True)

        elif re.search('Be the first to share your experience with this treatment', response.body):

            Effectiveness = ' '
            EaseofUse = ' '
            Satisfaction = ' '

            yield Request('http://www.webmd.com/search/2/api/rx/forms/v2/' + priceid, \
                          method='GET', headers=headers, \
                          callback=self.parse_prices, \
                          meta={'Condition': Condition, 'Drug': Drug, 'Indication': Indication, 'Type': Type,
                                'Review': Review, \
                                'Use': Use, \
                                'HowtoUse': HowtoUse, \
                                'Sides': Sides, \
                                'Precautions': Precautions, \
                                'Interactions': Interactions, \
                                'BrandName': BrandName, \
                                'GenName': GenName, \
                                'AvoidUse': AvoidUse, \
                                'Allergies': Allergies,
                                'Effectiveness': Effectiveness, \
                                'EaseofUse': EaseofUse, \
                                'Satisfaction': Satisfaction}, \
                          dont_filter=True)

        else:
            url = 'http://www.webmd.com/drugs/service/UserRatingService.asmx/GetUserReviewSummary?repositoryId=1&primaryId='  # 6007&secondaryId=-1&secondaryIdValue='
            url2 = '&secondaryId=-1&secondaryIdValue='
            id = re.search('(drugid=)(\d+)', response.url).group(2)
            id2 = urllib.quote(re.sub("\s+", " ", response.xpath('//option[@value = -1]//text()').extract()[0]).strip())


            yield Request(url + id + url2 + id2,\
                          callback= self.parse_ratings, \
                          meta={'Condition': Condition, 'Drug': Drug, 'Indication': Indication, 'Type': Type,
                                'Review': Review, \
                                'Use': Use, \
                                'HowtoUse': HowtoUse, \
                                'Sides': Sides, \
                                'Precautions': Precautions, \
                                'Interactions': Interactions, \
                                'BrandName': BrandName, \
                                'GenName': GenName, \
                                'AvoidUse': AvoidUse, \
                                'Allergies': Allergies, \
                                'priceid': priceid}, \
                          dont_filter=True)


    def parse_ratings(self, response):

        Condition = response.meta['Condition']
        Drug = response.meta['Drug']
        Indication = response.meta['Indication']
        Type = response.meta['Type']
        Review = response.meta['Review']
        Use = response.meta['Use']
        HowtoUse = response.meta['HowtoUse']
        Sides = response.meta['Sides']
        Precautions = response.meta['Precautions']
        Interactions = response.meta['Interactions']
        BrandName = response.meta['BrandName']
        GenName = response.meta['GenName']
        AvoidUse = response.meta['AvoidUse']
        Allergies = response.meta['Allergies']
        priceid = response.meta['priceid']

        if re.search('("xsd:string">)(\d+.\d+)',response.xpath('//*/*').extract()[3]):
            Effectiveness = re.search('("xsd:string">)(\d+.\d+)',response.xpath('//*/*').extract()[3]).group(2)
        else:
            Effectiveness = re.search('("xsd:string">)(\d+)',response.xpath('//*/*').extract()[3]).group(2)

        if re.search('("xsd:string">)(\d+.\d+)',response.xpath('//*/*').extract()[4]):
            EaseofUse = re.search('("xsd:string">)(\d+.\d+)',response.xpath('//*/*').extract()[4]).group(2)
        else:
            EaseofUse = re.search('("xsd:string">)(\d+)',response.xpath('//*/*').extract()[4]).group(2)

        if re.search('("xsd:string">)(\d+.\d+)',response.xpath('//*/*').extract()[5]):
            Satisfaction = re.search('("xsd:string">)(\d+.\d+)',response.xpath('//*/*').extract()[5]).group(2)
        else:
            Satisfaction = re.search('("xsd:string">)(\d+)',response.xpath('//*/*').extract()[5]).group(2)


        if priceid != '':
            yield Request('http://www.webmd.com/search/2/api/rx/forms/v2/'+priceid,\
                          method='GET', headers=headers, \
                          callback=self.parse_prices, \
                          meta={'Condition': Condition, 'Drug': Drug, 'Indication': Indication, 'Type': Type,
                                'Review': Review, \
                                'Use': Use, \
                                'HowtoUse': HowtoUse, \
                                'Sides': Sides, \
                                'Precautions': Precautions, \
                                'Interactions': Interactions, \
                                'BrandName': BrandName, \
                                'GenName': GenName, \
                                'AvoidUse': AvoidUse, \
                                'Allergies': Allergies,
                                'Effectiveness': Effectiveness,\
                                'EaseofUse': EaseofUse,\
                                'Satisfaction': Satisfaction}, \
                          dont_filter=True)

        else:
            strength = ' '
            form = ' '
            val = ' '
            EstimatedPrice = ' '
            item = WebmdItem()

            item['AvoidUse'] = AvoidUse
            item['Allergies'] = Allergies
            item['Use'] = Use
            item['HowtoUse'] = HowtoUse
            item['Precautions'] = Precautions
            item['Interactions'] = Interactions
            item['Sides'] = Sides
            item['Condition'] = Condition
            item['Drug'] = Drug
            item['Indication'] = Indication
            item['Type'] = Type
            item['Review'] = Review
            item['BrandName'] = BrandName
            item['GenName'] = GenName
            item['Effectiveness'] = Effectiveness
            item['EaseofUse'] = EaseofUse
            item['Satisfaction'] = Satisfaction
            item['EstimatedPrice'] = EstimatedPrice
            item['Dosage'] = strength
            item['PkgCount'] = val
            item['Form'] = form

            yield item


    def parse_prices(self, response):
        Condition = response.meta['Condition']
        Drug = response.meta['Drug']
        Indication = response.meta['Indication']
        Type = response.meta['Type']
        Review = response.meta['Review']
        Use = response.meta['Use']
        HowtoUse = response.meta['HowtoUse']
        Sides = response.meta['Sides']
        Precautions = response.meta['Precautions']
        Interactions = response.meta['Interactions']
        BrandName = response.meta['BrandName']
        GenName = response.meta['GenName']
        AvoidUse = response.meta['AvoidUse']
        Allergies = response.meta['Allergies']
        Effectiveness = response.meta['Effectiveness']
        EaseofUse = response.meta['EaseofUse']
        Satisfaction = response.meta['Satisfaction']

        if re.search('("NDC":\[")(\d+)', response.body):
            if re.search('("value":)(\d+)', response.body).group(2):

                ndc = re.search('("NDC":\[")(\d+)', response.body).group(2)
                val = re.search('("value":)(\d+)', response.body).group(2)

                if re.search('("form":")(\w+)', response.body):
                    form = re.search('("form":")(\w+)', response.body).group(2)
                else:
                    form = ' '

                if re.search('("strength":")(\d+\s+\w+)', response.body):
                    strength = re.search('("strength":")(\d+\s+\w+)', response.body).group(2)
                else:
                    strength = ' '

                urlp = 'http://www.webmd.com/search/2/api/rx/pricing/ndc/'
                urlp2 = '00000?lat=40.7466&lng=-73.9098&rad=5&rollup=true&pgroup='

                yield Request(urlp + ndc  + '/' + val + '/' + urlp2, \
                              method='GET',
                              headers=headers,
                              callback=self.parse_estprice,
                              meta={'Condition': Condition, 'Drug': Drug, 'Indication': Indication, 'Type': Type,
                                    'Review': Review, \
                                    'Use': Use, \
                                    'HowtoUse': HowtoUse, \
                                    'Sides': Sides, \
                                    'Precautions': Precautions, \
                                    'Interactions': Interactions, \
                                    'BrandName': BrandName, \
                                    'GenName': GenName, \
                                    'AvoidUse': AvoidUse, \
                                    'Allergies': Allergies,
                                    'Effectiveness': Effectiveness, \
                                    'EaseofUse': EaseofUse, \
                                    'Satisfaction': Satisfaction,\
                                    'strength': strength,\
                                    'val': val,\
                                    'form': form}, \
                              dont_filter=True)

            else:
                strength = ' '
                form = ' '
                val= ' '
                EstimatedPrice = ' '
                item = WebmdItem()

                item['AvoidUse'] = AvoidUse
                item['Allergies'] = Allergies
                item['Use'] = Use
                item['HowtoUse'] = HowtoUse
                item['Precautions'] = Precautions
                item['Interactions'] = Interactions
                item['Sides'] = Sides
                item['Condition'] = Condition
                item['Drug'] = Drug
                item['Indication'] = Indication
                item['Type'] = Type
                item['Review'] = Review
                item['BrandName'] = BrandName
                item['GenName'] = GenName
                item['Effectiveness'] = Effectiveness
                item['EaseofUse'] = EaseofUse
                item['Satisfaction'] = Satisfaction
                item['EstimatedPrice'] = EstimatedPrice
                item['Dosage'] = strength
                item['PkgCount'] = val
                item['Form'] = form

                yield item


    def parse_estprice(self,response):
        Condition = response.meta['Condition']
        Drug = response.meta['Drug']
        Indication = response.meta['Indication']
        Type = response.meta['Type']
        Review = response.meta['Review']
        Use = response.meta['Use']
        HowtoUse = response.meta['HowtoUse']
        Sides = response.meta['Sides']
        Precautions = response.meta['Precautions']
        Interactions = response.meta['Interactions']
        BrandName = response.meta['BrandName']
        GenName = response.meta['GenName']
        AvoidUse = response.meta['AvoidUse']
        Allergies = response.meta['Allergies']
        Effectiveness = response.meta['Effectiveness']
        EaseofUse = response.meta['EaseofUse']
        Satisfaction = response.meta['Satisfaction']
        strength = response.meta['strength']
        val = response.meta['val']
        form = response.meta['form']

        if re.search('("PharmacyGroupMinPrice":)(\d+.\d+)', response.body):
            EstimatedPrice = re.search('("PharmacyGroupMinPrice":)(\d+.\d+)', response.body).group(2)

            item = WebmdItem()

            item['AvoidUse'] = AvoidUse
            item['Allergies'] = Allergies
            item['Use'] = Use
            item['HowtoUse'] = HowtoUse
            item['Precautions'] = Precautions
            item['Interactions'] = Interactions
            item['Sides'] = Sides
            item['Condition'] = Condition
            item['Drug'] = Drug
            item['Indication'] = Indication
            item['Type'] = Type
            item['Review'] = Review
            item['BrandName'] = BrandName
            item['GenName'] = GenName
            item['Effectiveness'] = Effectiveness
            item['EaseofUse'] = EaseofUse
            item['Satisfaction'] = Satisfaction
            item['EstimatedPrice'] = EstimatedPrice
            item['Dosage'] = strength
            item['PkgCount'] = val
            item['Form'] = form

            yield item

        elif re.search('("PharmacyGroupMinPrice":)(\d+)', response.body):
            EstimatedPrice = re.search('("PharmacyGroupMinPrice":)(\d+)', response.body).group(2)

            item = WebmdItem()

            item['AvoidUse'] = AvoidUse
            item['Allergies'] = Allergies
            item['Use'] = Use
            item['HowtoUse'] = HowtoUse
            item['Precautions'] = Precautions
            item['Interactions'] = Interactions
            item['Sides'] = Sides
            item['Condition'] = Condition
            item['Drug'] = Drug
            item['Indication'] = Indication
            item['Type'] = Type
            item['Review'] = Review
            item['BrandName'] = BrandName
            item['GenName'] = GenName
            item['Effectiveness'] = Effectiveness
            item['EaseofUse'] = EaseofUse
            item['Satisfaction'] = Satisfaction
            item['EstimatedPrice'] = EstimatedPrice
            item['Dosage'] = strength
            item['PkgCount'] = val
            item['Form'] = form

            yield item

        else:
            EstimatedPrice = ' '

            item = WebmdItem()

            item['AvoidUse'] = AvoidUse
            item['Allergies'] = Allergies
            item['Use'] = Use
            item['HowtoUse'] = HowtoUse
            item['Precautions'] = Precautions
            item['Interactions'] = Interactions
            item['Sides'] = Sides
            item['Condition'] = Condition
            item['Drug'] = Drug
            item['Indication'] = Indication
            item['Type'] = Type
            item['Review'] = Review
            item['BrandName'] = BrandName
            item['GenName'] = GenName
            item['Effectiveness'] = Effectiveness
            item['EaseofUse'] = EaseofUse
            item['Satisfaction'] = Satisfaction
            item['EstimatedPrice'] = EstimatedPrice
            item['Dosage'] = strength
            item['PkgCount'] = val
            item['Form'] = form

            yield item