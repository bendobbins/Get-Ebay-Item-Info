from bs4 import BeautifulSoup as bs
import smtplib
import requests
import random

smtpServer = "smtp.gmail.com"
port = 465
# TODO
# I used gmail for these, might be able to use a different mail service
# If using gmail, must enable access to account from third party apps on sender email
senderEmail = "Email you want to send from"
receiverEmail = "Email you want to send to"
password = "Password for sender email"

def get_item_info_ebay(url):
    """
    Returns a list of dictionaries with information describing the items on the first page of the url searched that correspond
    to user keywords.
    """
    # Get site HTML
    website = requests.get(url).text
    siteHTML = bs(website, 'lxml')

    # Find all items listed on the first page of the search
    itemList = siteHTML.find_all("li")
    #itemList = siteHTML.find_all("li", {'class': "s-item s-item__pl-on-bottom s-item--watch-at-corner"})

    # Get information for items and return
    items = []
    for item in itemList:
        itemInfo = item_info(item)
        if itemInfo:
            items.append(itemInfo)
    return items


def item_info(item):
    """
    Return a dictionary with name (str), wear (str), image link (str), price (str), whether there is best offer (bool),
    whether there is bidding (bool and time (str)), and the return policy (bool) of an item if it has certain keywords in its name.
    """
    # Find name of item
    itemName = item.find("h3", {'class': "s-item__title"})

    if itemName:
        itemName = itemName.text
        # If item is one the user is looking for
        if find_item_ebay(itemName):
            # Gather info on item
            itemInfo = {}
            itemInfo["name"] = itemName
            itemWear = item.find("span", {'class': "SECONDARY_INFO"}).text
            itemInfo["wear"] = itemWear
            itemImage = item.find("img")
            itemInfo["image"] = itemImage["src"]
            # Replace html of prices with text
            itemPrices = replace(item.find_all("span", {'class': "s-item__price"}))
            itemInfo["prices"] = itemPrices
            itemInfo["bestOffer"] = False
            itemInfo["bidding"] = False
            itemInfo["returnPolicy"] = False

            # If there is more than one price for an item, there is bidding
            if len(itemPrices) > 1:
                itemInfo["bidding"] = True
                itemTime = item.find("span", {'class': "s-item__time-left"}).text
                itemInfo["time"] = itemTime

            else:
                itemBest = item.find("span", {'class': "s-item__purchase-options-with-icon"})
                # If there is a best offer section, set to true
                if itemBest:
                    itemInfo["bestOffer"] = True

            # Get return policy
            returns = return_possible(item)
            if returns:
                itemInfo["returnPolicy"] = True
                itemInfo["returns"] = returns
            
            return itemInfo
    # Return None if not looking for item according to keywords
    return None


def return_possible(item):
    """
    Get the return policy for an item and return it if it exists.
    """
    itemLink = item.find('a', {'class': "s-item__link"})

    if itemLink.has_attr("href"):
        # Get page for item
        itemPage = requests.get(itemLink["href"]).text
        itemHTML = bs(itemPage, 'lxml')
        # Find returns div
        returns = itemHTML.find("div", {'class': "ux-labels-values__values-content"})
        if returns:
            returnText = returns.find_all("span")
            # Return return policy
            for span in returnText:
                if "returns" in span.text.lower():
                    returnPolicy = span.text
                    return returnPolicy
    return None


def replace(priceList):
    """
    Replace html items in a list with the text inside them.
    """
    for i in range(len(priceList)):
        price = priceList.pop(i).text
        priceList.insert(i, price)
    return priceList


def find_item_ebay(item):
    """
    Returns True if one or more keywords is in item name, else False.
    """
    # TODO
    # Make a list of keywords, and the only items that you will get information about will be items with
    # those keywords in their name
    keywords = []
    for keyword in keywords:
        if keyword in item.lower():
            return True
    
    return False


def send_email(items):
    """
    Send email with info about items you want from sender email to receiver email.
    """
    stringList = []

    for item in items:
        # Clean up prices
        priceString = ""
        for price in item["prices"]:
            priceString += price + ", "
        priceString = priceString[:-2]

        # Gmail hides content that is the same in multiple chained emails, so I found that repeating this program
        # consistently would cause a lot of the info to be hidden when I received the email.
        # To combat this, there is a random number before each item so that gmail recognizes it as different content from the previous email
        x = random.randint(0, 1000)
        itemMessage = f"{x}: \n"

        # Start message with items that are always included
        itemMessage += f'Name: {item["name"]}\nImage: {item["image"]}\nPrice: {priceString}\nWear: {item["wear"]}\nBest Offer: {item["bestOffer"]}\n'

        # Check bidding and return policy, include corresponding info
        if item["bidding"]:
            itemMessage += f"Bidding: True\nTime: {item['time']}\n"
        else:
            itemMessage += "Bidding: False\n"
        if item["returnPolicy"]:
            itemMessage += f"Returns: {item['returns']}\n"

        # Make list of strings where each string is info for one item
        stringList.append(itemMessage)
    
    # Join strings and append with random number, again because of gmail hiding content
    joinedStrings = "\n".join(stringList)
    x = random.randint(0, 1000)
    joinedStrings += f"{x}\n"

    # TODO
    message = "Subject: YOUR SUBJECT\n\n" + joinedStrings

    # Try connecting to mail server, sending email
    try:
        server = smtplib.SMTP_SSL(smtpServer, port)
        server.ehlo()
        server.login(senderEmail, password)
        server.ehlo()
        server.sendmail(senderEmail, receiverEmail, message)
    
    except Exception as e:
        raise

    # Always quit server
    finally:
        server.quit()



def main():
    # TODO
    # Look up a search query on Ebay, paste the url below
    # Ex: https://www.ebay.com/sch/i.html?_from=R40&_trksid=p2380057.m570.l1313&_nkw=basketball&_sacat=0
    ebayUrl = 'Your Ebay Search'
    send_email((get_item_info_ebay(ebayUrl)))



if __name__ == "__main__":
    main()