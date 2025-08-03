from lxml import etree

def parse_searched_friend(html: str):
    # TODO: icon, trophy, etc parsing, cv needed.
    tree = etree.HTML(html)
    name_ele = tree.xpath('//div[@class="name_block f_l f_16"]')[0]
    rating_ele = tree.xpath('//div[@class="rating_block"]')[0]
    return {
        "name": name_ele.text,
        "rating": int(rating_ele.text)
    }
