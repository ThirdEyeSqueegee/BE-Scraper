import scrapy


class SpiderSpider(scrapy.Spider):
    name = 'spider'
    allowed_domains = ['4specs.com']
    start_urls = ['http://4specs.com/s/']

    # Creates a list of all the item URLS on the main page and passes control to a
    # callback for each item
    def parse(self, response):
        # Select all <a> tags by their href attribute
        items = response.css("a::attr(href)").getall()
        for item in items:
            url = response.urljoin(item)
            # Pass the item URL into the callback
            yield scrapy.Request(url, callback=self.parse_vendors, cb_kwargs=dict(item_url=url))
    
    # Parses the vendor page that its caller's item URL points to
    def parse_vendors(self, response, item_url):
        # Select the contents of an <h1> tag -- the ID and name of the item
        item = response.css('h1::text').get().split(' - ')
        item_number = item[0]
        item_name = item[1]
        # Select the text of all <a> tags -- the name of the company that sells the item
        vendors = response.css('div.listings > ul > li > a::text').getall()
        # Select all <a> tags by their href attribute -- the URL of the company that
        # sells the item
        vendorlinks = response.css('div.listings > ul > li > a::attr(href)').getall()
        # Create a dict by mapping each element of vendors to each member of vendorlinks
        vendordict = dict(zip(vendors, vendorlinks))

        # yield a dict in the final format that will be saved to a JSON file
        yield {
            'itemNumber': item_number,
            'itemName': item_name,
            'itemURL': item_url,
            'vendors': vendordict,
        }
