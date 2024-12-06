# *  Instalando pacotes

# pip install selenium webdriver-manager beautifulsoup4 pandas numpy

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime

# Função para extrair títulos dos anúncios
def get_ad_titles(ads):
    for ad in ads:
        title = ad.find('h2', {'class': 'sc-i1odl-11 kvKUxE'})
        title = title.text.strip() if title else np.nan
        yield title

# Função para extrair bairros dos anúncios
def get_ad_neighborhoods(ads):
    for ad in ads:
        location = ad.find('h2', {'data-qa': 'POSTING_CARD_LOCATION'})
        if location:
            location_text = location.text.strip()
            neighborhoods = location_text.split(',')[0]  # Pega a parte antes da vírgula
        else:
            neighborhoods = np.nan
        yield neighborhoods

# Função para extrair detalhes dos anúncios (área total, quartos, banheiros, garagem)
def get_ad_details(ads):
    for ad in ads:
        try:
            # Encontrar todos os elementos com a classe comum
            features = ad.find_all('span', {'class': 'postingMainFeatures-module__posting-main-features-span__ror2o postingMainFeatures-module__posting-main-features-listing__BFHHQ'})
            
            # Inicializar variáveis
            total_area = np.nan
            bedrooms = np.nan
            bathrooms = np.nan
            garage = 0
            
            # Iterar sobre os elementos encontrados e extrair informações
            for feature in features:
                text = feature.text.strip()
                if 'm² tot.' in text:
                    total_area = re.search(r'\d+', text)
                    total_area = int(total_area.group()) if total_area else np.nan
                elif 'quartos' in text:
                    bedrooms = re.search(r'\d+', text)
                    bedrooms = int(bedrooms.group()) if bedrooms else np.nan
                    if bedrooms == 0:
                        bedrooms = 1
                elif 'banheiro' in text:
                    bathrooms = re.search(r'\d+', text)
                    bathrooms = int(bathrooms.group()) if bathrooms else np.nan
                elif 'vaga' in text:
                    garage = re.search(r'\d+', text)
                    garage = int(garage.group()) if garage else 0
        
        except Exception as e:
            print(f"Erro ao extrair detalhes: {e}")
        
        yield total_area, bedrooms, bathrooms, garage

# Função para extrair valores dos anúncios (aluguel e taxa de condomínio)
def get_ad_values(ads):
    for ad in ads:
        try:
            rent = ad.find('div', {'data-qa': 'POSTING_CARD_PRICE'})
            rent = rent.text.strip() if rent else np.nan
            condo_fee = ad.find('div', {'data-qa': 'expensas'})
            condo_fee = condo_fee.text.strip() if condo_fee else np.nan
        except Exception as e:
            print(f"Erro ao extrair valores: {e}")
            rent = np.nan
            condo_fee = np.nan
        yield rent, condo_fee

# Função para extrair links dos anúncios
def get_ad_links(ads):
    for ad in ads:
        try:
            link = ad.find('a', {'data-qa': 'POSTING_CARD_DESCRIPTION'})
            link = link['href'] if link else np.nan
        except Exception as e:
            print(f"Erro ao extrair link: {e}")
            link = np.nan
        yield link

# Função principal para extrair anúncios de várias páginas
def scrape_apartment_ads(starter_page, final_page):
    # Inicialização de um dicionário para armazenar os dados de anúncios de apartamentos
    apartment_df = {'Title': [], 'Neighborhood': [], 'Total Area': [], 'Useful Area': [], 'Bedrooms': [], 'Bathrooms': [], 'Garage': [], 'Rent': [], 'Condo Fee': [], 'Link': []}
    
    chrome_service = Service(ChromeDriverManager().install())
    chrome_options = Options()
    # Remova a opção headless para permitir a interação manual
    # chrome_options.add_argument("--headless")  # Comentado para permitir a interação manual
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Desabilitar a detecção de automação
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    ]

    # Gerar um timestamp para o nome do arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'apartment_ads_{timestamp}.csv'

    # Loop para extrair informações dos anúncios das páginas e adicioná-las ao Dicionário de anúncios de apartamentos
    for page in range(starter_page, final_page):
        url = f'https://www.imovelweb.com.br/apartamentos-aluguel-sao-paulo-sp-ordem-precio-menor-pagina-{page}.html'
    
        chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        driver.get(url)
        driver.implicitly_wait(5)
        
        # Aceitar cookies
        try:
            accept_cookies_button = driver.find_element(By.XPATH, "//button[@data-qa='cookies-policy-banner' and contains(text(), 'Aceito')]")
            accept_cookies_button.click()
            time.sleep(2)  # Esperar um pouco para garantir que a ação foi concluída
        except Exception as e:
            print("Botão de aceitação de cookies não encontrado ou erro ao clicar:", e)
        
        # Verificar a presença do CAPTCHA e pausar até que ele seja resolvido
        while True:
            try:
                captcha_element = driver.find_element(By.XPATH, "//div[contains(@class, 'captcha')]")
                print("CAPTCHA detectado. Por favor, resolva o CAPTCHA manualmente.")
                time.sleep(5)  # Esperar 5 segundos antes de verificar novamente
            except:
                break  # CAPTCHA não encontrado, continuar a execução

        page_content = driver.page_source
        soup = BeautifulSoup(page_content, 'html.parser')
        ads = soup.find_all('div', {'class': 'CardContainer-sc-1tt2vbg-5 fvuHxG'})
        
        for title in get_ad_titles(ads):
            apartment_df['Title'].append(title)
            
        for neighborhood in get_ad_neighborhoods(ads):
            apartment_df['Neighborhood'].append(neighborhood)
            
        for detail in get_ad_details(ads):
            apartment_df['Total Area'].append(detail[0])
            apartment_df['Useful Area'].append(np.nan)  # Adiciona um valor padrão para 'Useful Area'
            apartment_df['Bedrooms'].append(detail[1])
            apartment_df['Bathrooms'].append(detail[2])
            apartment_df['Garage'].append(detail[3])
            
        for value in get_ad_values(ads):
            apartment_df['Rent'].append(value[0])
            apartment_df['Condo Fee'].append(value[1])
            
        for link in get_ad_links(ads):
            apartment_df['Link'].append(link)

        driver.quit()
        time.sleep(random.uniform(5, 10))  # Atraso aleatório entre 5 e 10 segundos
        
        # Transformação do dicionário de anúncios de apartamentos em um DataFrame Pandas
        df = pd.DataFrame(apartment_df)
        
        # Salvar o DataFrame em um arquivo CSV após cada página
        df.to_csv(filename, index=False, mode='a', header=not pd.io.common.file_exists(filename))
        
    return df

# Execução da função principal para extrair anúncios de 1.000 páginas
apartment_df = scrape_apartment_ads(1, 1001)

# Exibição do DataFrame resultante
print(apartment_df)

# Informações do DataFrame
print(apartment_df.info())

# Verificação de duplicatas no DataFrame
print(apartment_df[apartment_df.duplicated()])

# Número de links exclusivos
print(apartment_df['Link'].nunique())

# Número de links duplicados
print(len(apartment_df[apartment_df['Link'].duplicated()]))

# Remoção de duplicatas com base na coluna de links
apartment_df = apartment_df.drop_duplicates(subset=['Link'])

# Verificação de duplicatas após a remoção
print(len(apartment_df[apartment_df.duplicated()]))

# Conversão de algumas colunas para o tipo de número inteiro
apartment_df['Total Area'] = apartment_df['Total Area'].astype(pd.Int64Dtype())
apartment_df['Useful Area'] = apartment_df['Useful Area'].astype(pd.Int64Dtype())
apartment_df['Bedrooms'] = apartment_df['Bedrooms'].astype(pd.Int64Dtype())
apartment_df['Bathrooms'] = apartment_df['Bathrooms'].astype(pd.Int64Dtype())

# Salvar o DataFrame em um arquivo CSV
apartment_df.to_csv(filename, index=False)
