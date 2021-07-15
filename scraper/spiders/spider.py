import scrapy


class SpiderSpider(scrapy.Spider):
    name = "spider"
    allowed_domains = ["4specs.com"]
    start_urls = ["http://4specs.com/s/"]

    # Creates a list of all the item URLS on the main page and passes control to a
    # callback for each item
    def parse(self, response):
        # Select all <a> tags by their href attribute
        items = response.css("div.listings a::attr(href)").getall()
        for item in items:
            url = response.urljoin(item)
            # Pass the item URL into the callback
            yield scrapy.Request(
                url, callback=self.parse_items, cb_kwargs=dict(item_url=url)
            )

    # Parses the vendor page that its caller's item URL points to
    def parse_items(self, response, item_url):
        # Select the contents of an <h1> tag -- the ID and name of the item
        item = response.css("div.listings > h1::text").get().split(" - ")
        item_number = item[0]
        item_name = item[1]
        # Select the text of all <a> tags -- the name of the company that sells the item
        vendors = response.css("div.listings > ul > li > a::text").getall()
        described_vendors = []
        # Mark the vendors which have associated descriptions
        for vendor in response.css("div.listings > ul > li"):
            if vendor.css("li::text") != []:
                described_vendors.append(vendor.css("a::text").get())

        # Select all <a> tags by their href attribute -- the URL of the company that
        # sells the item
        vendor_links = response.css("div.listings > ul > li > a::attr(href)").getall()
        vendor_desc = response.css("div.listings > ul > li::text").getall()
        vendor_desc = [desc[3:] for desc in vendor_desc if desc[1] == "-"]
        vendor_values = [
            {"URL": url, "desc": None, "image": None} for url in vendor_links
        ]

        # Create a dict by mapping each element of vendors to each member of vendorlinks
        vendor_dict = dict(zip(vendors, vendor_values))

        # Add descriptions to vendors that have associated descriptions
        for (k, v) in vendor_dict.items():
            if k in described_vendors:
                v["desc"] = vendor_desc.pop(0)

        # yield a dict in the final format that will be saved to a JSON file
        yield {
            "itemNumber": item_number,
            "itemName": item_name,
            "itemURL": item_url,
            "vendors": vendor_dict,
        }
