# Scraper-Imovelweb-
# Web Scraper de Anúncios de Apartamentos - ImovelWeb

Desenvolvi como treinamento, um scraping capaz de buscar imóveis da plataforma ImovelWeb. Adicionei atrasos e configurações manuais de CAPTCHA para simular o comportamento humano e desenvolvi a ferramenta com o objetivo de mapear as faixas de preços dos imóveis, separando-os por bairros em São Paulo. Consegui uma cadência de 20 páginas entre 5 a 10 segundos, configuradas para serem salvas em arquivos CSV.

## Etapa a Etapa do Projeto
Este README detalha cada etapa do projeto para facilitar a compreensão e apresentação em meu portfólio.

### 1. Instalação dos Pacotes Necessários
Antes de começar, é necessário instalar alguns pacotes Python. Você pode fazer isso rodando o comando:
```bash
pip install selenium webdriver-manager beautifulsoup4 pandas numpy
```
Estes pacotes serão usados para controlar o navegador, extrair dados das páginas, organizar os dados e salvar os resultados.

### 2. Configuração do WebDriver
Para navegar no site, é necessário configurar o WebDriver (neste caso, do Chrome). Utilizei o `webdriver-manager` para facilitar a instalação do driver e evitar problemas de compatibilidade.

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
```
A função `configure_driver()` é responsável por inicializar o ChromeDriver com opções para que a automação não seja detectada pelo site.

### 3. Aceitação de Cookies
Muitos sites utilizam cookies e pedem que os usuários aceitem esses termos ao acessar pela primeira vez. Adicionei a função `accept_cookies(driver)` que verifica se o botão de cookies está presente e o clica automaticamente.

```python
def accept_cookies(driver):
    try:
        accept_cookies_button = driver.find_element(By.XPATH, "//button[@data-qa='cookies-policy-banner' and contains(text(), 'Aceito')]")
        accept_cookies_button.click()
        time.sleep(2)  # Espera para garantir que a ação seja concluída
    except Exception as e:
        print("Botão de aceitação de cookies não encontrado ou erro ao clicar:", e)
```

### 4. Controle de CAPTCHA
Como medida para impedir automatizações, o site pode mostrar um CAPTCHA. A função `handle_captcha(driver)` foi desenvolvida para pausar a execução do código até que o CAPTCHA seja resolvido manualmente.

```python
def handle_captcha(driver):
    while True:
        try:
            driver.find_element(By.XPATH, "//div[contains(@class, 'captcha')]")
            print("CAPTCHA detectado. Por favor, resolva o CAPTCHA manualmente.")
            time.sleep(5)  # Espera 5 segundos antes de verificar novamente
        except:
            break  # CAPTCHA não encontrado, continuar a execução
```

### 5. Extração dos Dados dos Anúncios
A função `extract_ad_data(ads)` extrai informações dos anúncios, como título, localização, área total, quartos, banheiros, valor do aluguel, taxa de condomínio e link para o anúncio. Utilizei o BeautifulSoup para fazer o parsing do conteúdo HTML e buscar os dados relevantes.

```python
def extract_ad_data(ads):
    for ad in ads:
        title = ad.find('h2', {'class': 'sc-i1odl-11 kvKUxE'})
        title = title.text.strip() if title else np.nan

        location = ad.find('h2', {'data-qa': 'POSTING_CARD_LOCATION'})
        neighborhood = location.text.strip().split(',')[0] if location else np.nan

        features = ad.find_all('span', {'class': 'postingMainFeatures-module__posting-main-features-span__ror2o postingMainFeatures-module__posting-main-features-listing__BFHHQ'})
        total_area, bedrooms, bathrooms, garage = np.nan, np.nan, np.nan, 0

        for feature in features:
            text = feature.text.strip()
            if 'm² tot.' in text:
                total_area = int(re.search(r'\d+', text).group()) if re.search(r'\d+', text) else np.nan
            elif 'quartos' in text:
                bedrooms = int(re.search(r'\d+', text).group()) if re.search(r'\d+', text) else np.nan
                if bedrooms == 0:
                    bedrooms = 1
            elif 'banheiro' in text:
                bathrooms = int(re.search(r'\d+', text).group()) if re.search(r'\d+', text) else np.nan
            elif 'vaga' in text:
                garage = int(re.search(r'\d+', text).group()) if re.search(r'\d+', text) else 0

        rent = ad.find('div', {'data-qa': 'POSTING_CARD_PRICE'})
        rent = rent.text.strip() if rent else np.nan

        condo_fee = ad.find('div', {'data-qa': 'expensas'})
        condo_fee = condo_fee.text.strip() if condo_fee else np.nan

        link = ad.find('a', {'data-qa': 'POSTING_CARD_DESCRIPTION'})
        link = link['href'] if link else np.nan

        yield {
            'Title': title,
            'Neighborhood': neighborhood,
            'Total Area': total_area,
            'Useful Area': np.nan,
            'Bedrooms': bedrooms,
            'Bathrooms': bathrooms,
            'Garage': garage,
            'Rent': rent,
            'Condo Fee': condo_fee,
            'Link': link
        }
```

### 6. Loop Principal para Navegar nas Páginas
A função principal `scrape_apartment_ads(start_page, end_page)` é responsável por iterar pelas páginas de anúncios e extrair os dados.
- Para cada página, configuramos o driver, navegamos até a URL e chamamos as funções auxiliares para aceitar cookies e lidar com o CAPTCHA.
- Após a extração dos dados, salvamos em um arquivo CSV.

```python
def scrape_apartment_ads(start_page, end_page):
    apartment_data = []
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    ]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'apartment_ads_{timestamp}.csv'

    for page in range(start_page, end_page):
        url = f'https://www.imovelweb.com.br/apartamentos-aluguel-sao-paulo-sp-ordem-precio-menor-pagina-{page}.html'
        driver = configure_driver()
        driver.get(url)
        driver.implicitly_wait(5)

        # Configuração de User-Agent
        chrome_options = Options()
        chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')

        accept_cookies(driver)
        handle_captcha(driver)

        # Coletar conteúdo da página
        page_content = driver.page_source
        soup = BeautifulSoup(page_content, 'html.parser')
        ads = soup.find_all('div', {'class': 'CardContainer-sc-1tt2vbg-5 fvuHxG'})

        # Extrair informações dos anúncios e armazenar
        for ad_data in extract_ad_data(ads):
            apartment_data.append(ad_data)

        driver.quit()
        time.sleep(random.uniform(5, 10))  # Atraso aleatório entre 5 e 10 segundos

        # Salvar os dados em CSV a cada página
        df = pd.DataFrame(apartment_data)
        df.to_csv(filename, index=False, mode='a', header=not pd.io.common.file_exists(filename))

    return pd.DataFrame(apartment_data)
```

### 7. Execução do Script e Processamento dos Dados
Depois de extrair os dados, removemos duplicatas e salvamos um arquivo CSV final, com os dados organizados.

```python
if __name__ == "__main__":
    apartment_df = scrape_apartment_ads(1, 1001)

    # Exibe informações do DataFrame resultante
    print(apartment_df.info())

    # Remove duplicatas com base no link do anúncio
    apartment_df = apartment_df.drop_duplicates(subset=['Link'])

    # Converte colunas para o tipo inteiro, onde aplicável
    for column in ['Total Area', 'Useful Area', 'Bedrooms', 'Bathrooms']:
        apartment_df[column] = apartment_df[column].astype(pd.Int64Dtype())

    # Salva o DataFrame final em CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'apartment_ads_cleaned_{timestamp}.csv'
    apartment_df.to_csv(filename, index=False)
    print(f"Dados salvos em {filename}")
```

## Tecnologias Utilizadas
- **Selenium**: Para automatizar a navegação nas páginas do site.
- **BeautifulSoup**: Para fazer o parsing do conteúdo HTML e extrair as informações desejadas.
- **Pandas**: Para organização e armazenamento dos dados extraídos em um DataFrame e salvamento em CSV.
- **webdriver-manager**: Para gerenciar a instalação do ChromeDriver.

## Observações
- O código foi desenvolvido para fins educacionais e deve ser utilizado de acordo com as políticas do site ImovelWeb.
- Pode ser necessário ajustar a identificação dos elementos conforme o site sofra atualizações.

## Autor
- **Eduardo Mesquita** - [LinkedIn](https://www.linkedin.com/in/engeduardomesquita)

## Licença
Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## Exemplo da Base de Dados Extraída
Um exemplo do formato da base de dados gerada pode ser encontrado em: https://github.com/Edumesqg/Scraper-Imovelweb-/blob/main/apartment_ads_20241206_180156.csv
Ele contém algumas linhas dos dados extraídos, incluindo informações como título, bairro, área total, valor do aluguel, etc.
