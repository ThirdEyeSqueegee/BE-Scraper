import scrapy
from urllib import parse


class SpecSpider(scrapy.Spider):
    name = "4specs_spider"
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
        item_number = item[0].replace(" ", "")
        item_name = item[1]
        # Select the text of all <a> tags -- the name of the company that sells the item
        vendors = response.css("div.listings > ul > li > a::text").getall()
        if len(vendors) != 0:
            described_vendors = []
            # Mark the vendors which have associated descriptions
            for vendor in response.css("div.listings > ul > li"):
                if vendor.css("li::text") != []:
                    described_vendors.append(vendor.css("a::text").get())

            # Select all <a> tags by their href attribute -- the URL of the company that
            # sells the item
            vendor_links = response.css(
                "div.listings > ul > li > a::attr(href)"
            ).getall()
            vendor_desc = response.css("div.listings > ul > li::text").getall()
            vendor_desc = [s for s in vendor_desc if s != "" and s != " " and s != "\n"]
            vendor_desc = [desc[3:] for desc in vendor_desc if desc[1] == "-"]
            vendor_values = [
                {"URL": url, "desc": None, "image": None} for url in vendor_links
            ]

            # Create a dict by mapping each element of vendors to each member of
            # vendor_links
            vendor_dict = dict(zip(vendors, vendor_values))

            # Add descriptions to vendors that have associated descriptions
            for (k, v) in vendor_dict.items():
                if k in described_vendors:
                    if len(vendor_desc) == 0:
                        break
                    v["desc"] = vendor_desc.pop(0)

        f_vendors = response.css("div.mfg_div > p > a > strong::text").getall()
        f_vendor_links = response.css("div.mfg_div > p > a::attr(href)").getall()
        f_vendor_images = response.css("div.mfg_div img::attr(src)").getall()
        f_vendor_images = [
            "https://www.4specs.com" + img_url[5:] for img_url in f_vendor_images
        ]
        f_vendor_desc = response.css(
            "div.mfg_div > p::text, div.mfg_div > p > strong::text"
        ).getall()

        # Remove duplicates while preserving the order of elements in each list
        f_vendors = list(dict.fromkeys(f_vendors))
        f_vendor_links = list(dict.fromkeys(f_vendor_links))
        f_vendor_images = list(dict.fromkeys(f_vendor_images))

        f_vendor_desc = [s.strip() for s in " ".join(f_vendor_desc).split("\n")]

        if " -  CA, AZ, NV, NM, UT & CO " in f_vendor_desc:
            f_vendor_desc.remove(" -  CA, AZ, NV, NM, UT & CO ")
        f_vendor_desc = [s for s in f_vendor_desc if s != ""]

        f_vendor_desc = list(dict.fromkeys(f_vendor_desc))

        f_vendor_dict = {}
        for i in range(len(f_vendors)):
            f_vendor_dict[f_vendors[i]] = {}
            f_vendor_dict[f_vendors[i]]["url"] = f_vendor_links[i]
            f_vendor_dict[f_vendors[i]]["desc"] = f_vendor_desc[i]
            f_vendor_dict[f_vendors[i]]["image"] = f_vendor_images[i]

        if len(vendors) == 0:
            vendor_dict = f_vendor_dict
        else:
            vendor_dict = dict(vendor_dict, **f_vendor_dict)

        # yield a dict in the final format that will be saved to a JSON file
        yield {
            "csi_number": item_number,
            "item_name": item_name,
            "item_url": item_url,
            "vendors": vendor_dict,
        }


class SweetsSpider(scrapy.Spider):
    name = "sweets_spider"
    allowed_domains = ["sweets.construction.com"]
    start_urls = ["https://sweets.construction.com"]

    def parse(self, response):
        products = "https://sweets.construction.com/BrowseByDivision"
        yield scrapy.Request(products, callback=self.parse_divisions)

    def parse_divisions(self, response):
        div_names = response.css("td.col-1 > a::text").getall()
        div_names = [name[11:] for name in div_names]
        div_links = response.css("td.col-1 > a::attr(href)").getall()
        div_links = ["https://sweets.construction.com" + url for url in div_links]
        divs = dict(zip(div_names, div_links))

        for name, url in divs.items():
            yield scrapy.Request(
                url, callback=self.parse_subdivisions, cb_kwargs=dict(div=name)
            )

    def parse_subdivisions(self, response, div):
        subdiv_names = response.css("td.col-1 > a::text").getall()
        subdiv_numbers = [
            name.split(" - ")[0].replace(" ", "") for name in subdiv_names
        ]
        subdiv_names = [name.split(" - ")[-1].strip() for name in subdiv_names]
        subdivs = list(zip(subdiv_numbers, subdiv_names))
        subdiv_links = response.css("td.col-1 > a::attr(href)").getall()
        subdiv_links = ["https://sweets.construction.com" + url for url in subdiv_links]
        subdivs_dict = dict(zip(subdivs, subdiv_links))

        for subdiv, url in subdivs_dict.items():
            yield scrapy.Request(
                url,
                callback=self.parse_products,
                cb_kwargs=dict(div=div, csi=subdiv[0], subdiv=subdiv[1]),
            )

    def parse_products(self, response, div, csi, subdiv):
        product_names = response.css("a.product-name::text").getall()
        product_names = [name.split(" - ")[-1].strip() for name in product_names]
        product_names = [
            name.encode("ascii", "ignore").decode() for name in product_names
        ]
        product_links = response.css("a.product-name::attr(href)").getall()
        product_links = [
            "https://sweets.construction.com" + url for url in product_links
        ]
        products = dict(zip(product_names, product_links))

        for name, url in products.items():
            yield scrapy.Request(
                url,
                callback=self.parse_item,
                cb_kwargs=dict(div=div, csi=csi, subdiv=subdiv, product=name),
            )

    def parse_item(self, response, div, csi, subdiv, product):
        manufacturer = response.css("div.productInfo span.company-name::text").get()
        manufacturer = manufacturer[:-2]
        manufacturer_url = response.css("a.locate_dis::attr(href)").get()
        overview = response.css("div.prd-overview > p:nth-child(1)::text").get()
        overview = overview.encode("ascii", "ignore").decode().strip()
        url = response.request.url
        image = response.xpath("//*[@class='item active srle']/img/@src").get()
        product_page = response.css("p.manufacturerLink > a::attr(href)").get()

        if product_page[:15] == "/AdditionalInfo":
            product_page = product_page[16:]
            product_page = parse.unquote(product_page)

        # Optional full description, recommend leaving this out to prevent bloating
        description = " ".join(
            response.css("#overviewContent > p::text").getall()
        ).strip()

        yield {
            "division": div,
            "subdivision": subdiv,
            "manufacturer": manufacturer,
            "manufacturer_url": manufacturer_url,
            "name": product,
            "csi_number": csi,
            "product_page": product_page,
            "image": image,
            "url": url,
            "overview": overview,
        }
