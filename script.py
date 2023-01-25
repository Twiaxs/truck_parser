import json
import os
import asyncio
import aiohttp
import aiofiles
from tqdm import tqdm
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

headers = UserAgent()

class GetUrlsParser:
    def __init__(self):
        self.headers = {'User-Agent': headers.ie}
        self.__links = 'https://www.truckscout24.de/transporter/gebraucht/kuehl-iso-frischdienst/renault'
        
    async def get_urls(self):
        urls = []
        for page_num in range(1,5):
            async with aiohttp.ClientSession() as session:
                response = await session.get(f'{self.__links}?currentpage={page_num}', headers=self.headers)
                soup = BeautifulSoup(await response.text(), 'lxml')
                url = soup.find(attrs={'data-item-name': 'detail-page-link'})
                urls.append(url.get('href').replace('\xfc', ''))
        return urls

class GetDataParser(GetUrlsParser):
    async def get_data(self):
        data = []
        for url in await self.get_urls():
            async with aiohttp.ClientSession() as session:
                response = await session.get(url=f'https://www.truckscout24.de{url}', headers=self.headers)
                soup = BeautifulSoup(await response.text(), 'lxml')
                find_id = soup.find_all(class_="sc-btn-ross-ghost")[1].get('href')
                id = str(find_id).partition('ID')[2].replace('=','')
                title = soup.find(class_='sc-ellipsis sc-font-xl').text
                price = soup.find(class_='sc-highlighter-4 sc-highlighter-xl sc-font-bold').text.replace(',-', '').replace('€ ', '').replace('.', '')
                description = soup.find(attrs={'data-item-name': 'description'}).text.replace('\r\n', ' ').replace('\n','')
                data_basic = soup.findAll(class_='itemval')
                li = soup.find('ul', class_='columns').text

                try:
                    mileage = data_basic[1].text.replace(' km', '').replace('.', '')
                except:
                    mileage = None

                if "Farbe" in li:
                    color = li[li.find("Farbe") + 6:].partition('\n')[0]
                else:
                    color = None

                if "Leistung" in li:
                    power = int(li[li.find("Leistung") + 8:].partition('kW')[0].replace("\n", ''))
                else:
                    power = None

                data.append({
                    "id":int(id),
                    "href":url,
                    "title":title,
                    "price":int(price),
                    "mileage":int(mileage),
                    "color": color,
                    "power": power,
                    "description":description
                })
        return data

    async def get_photos(self):
        for url in await self.get_urls():
            async with aiohttp.ClientSession() as session:
                response = await session.get(url=f'https://www.truckscout24.de{url}', headers=self.headers)
                soup = BeautifulSoup(await response.text(), 'lxml')
                find_id = soup.find_all(class_="sc-btn-ross-ghost")[1].get('href')
                id = str(find_id).partition('ID')[2].replace('=','')
                try:
                    os.mkdir(id)
                except FileExistsError:
                    print("Такая папка создана")
                for index in tqdm(range(1,4)):
                    img = soup.find_all(attrs={'class': 'gallery-picture__image sc-lazy-image lazyload'})[index]
                    img_file = await session.get(img.get('data-src'))
                    async with aiofiles.open(f"{str(id)}/img{index}.jpg", "wb") as file:
                        file.write(img_file)
                        
class Json:
    def write(self):
        with open("news_dict.json", "w", encoding="utf-8") as file:
            json.dump({"ads":asyncio.run(GetDataParser().get_data())}, file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(GetDataParser().get_photos())
    Json().write()

    



    



    



    
