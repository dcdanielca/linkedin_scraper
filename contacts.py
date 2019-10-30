from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
from getpass import getpass

import time
import os
import random
import pandas as pd
import glob
import re 


def login():
    email = input("Ingrese email: ")
    password = getpass("Ingrese password: ")

    # Abriendo navegador
    browser = webdriver.Chrome(os.getcwd() + '/chromedriver')
    browser.get("https://www.linkedin.com")
    browser.maximize_window()
    browser.implicitly_wait(2)

    # Realizando login
    email_element = browser.find_element_by_name("session_key")
    email_element.send_keys(email)
    pass_element = browser.find_element_by_name("session_password")
    pass_element.send_keys(password)
    pass_element.submit()
    browser.implicitly_wait(3)
    return browser

def get_info_contacts(browser, df):
    count = 1
    contacts = df[df['scrapeado?'] == False].values
    # Extraer informacion de contacto
    for index, contact in enumerate(contacts):
        if count % 100 == 0:
            browser.close()
            browser = login()
        browser.get(contact[1] + "detail/contact-info/")
        browser.implicitly_wait(3)
        contact_page = bs(browser.page_source, features="html.parser")

        # Nombre
        name_elements = contact_page.find_all("h1", id="pv-contact-info")
        for name in name_elements:
            df.loc[index, 'nombre'] = name.get_text()

        # Email
        email_elements = contact_page.find_all('a', href=re.compile("mailto"))
        for email in email_elements:
            df.loc[index, 'email'] = email.get('href')[7:]

        # Celular
        phone_section = contact_page.find_all("section", {"class": "pv-contact-info__contact-type ci-phone"})
        if len(phone_section) != 0:
            phone = phone_section[0].find_all("span",{"class": "t-14 t-black t-normal"})
            df.loc[index, 'celular'] = phone[0].get_text()

        job_section = contact_page.find_all("section", {"class": "pv-profile-section experience-section ember-view"})
        if len(job_section) != 0:
            first_job = job_section[0].find_all('section', {'class': 'pv-profile-section__sortable-card-item pv-profile-section pv-position-entity ember-view'})
            if len(first_job) != 0:
                first_job = first_job[0]
            else:
                first_job = job_section[0].find_all('section', {'class': 'pv-profile-section__card-item-v2 pv-profile-section pv-position-entity ember-view'})[0]

            # Cargo y empresa
            company = first_job.find_all('p', {'class': "pv-entity__secondary-title t-14 t-black t-normal"})
            if len(company) != 0:
                df.loc[index, 'empresa'] = company[0].get_text()
                position = first_job.find_all('h3', {'class': "t-16 t-black t-bold"})
                df.loc[index, 'cargo'] = position[0].get_text()
            else:
                company = first_job.find_all('h3', {'class': "t-16 t-black t-bold"}) 
                df.loc[index, 'empresa'] = company[0].find_all('span')[1].get_text()
                position = first_job.find_all('h3', {'class': 't-14 t-black t-bold'})
                df.loc[index, 'cargo'] = position[0].find_all('span')[1].get_text()
        df.loc[index, 'scrapeado?'] = True
        df.to_csv('contacts.csv', index=False)
        count +=1
        # wait few seconds before to connect to the next profile
        time.sleep(random.uniform(0.5, 1.9))

def get_all_contacts():

    browser = login()

    # Verificando que no existe csv con contactos para no sobrescribir información
    existent_csv = glob.glob('contacts.csv')
    if len(existent_csv) != 0:
        df = pd.read_csv('contacts.csv')
        get_info_contacts(browser, df)
        return

    browser.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")

    # Haciendo scroll para obetener todos los contactos
    last_height = 0
    while True:
        # Scroll down to bottom
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(random.uniform(2.5, 4.9))
        # Calculate new scroll height and compare with total scroll height
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Patrón de links de contactos 
    page = bs(browser.page_source, features="html.parser")
    content = page.find_all('a', {'class':"mn-connection-card__link ember-view"})
    mynetwork = []
    for contact in content:
        mynetwork.append('https://www.linkedin.com' + contact.get('href'))

    # Creando csv con la información de contactos
    df = pd.DataFrame(columns = ['scrapeado?', 'link', 'nombre', 'empresa', 'cargo', 'celular', 'email'])
    df['link'] = mynetwork
    df['scrapeado?'] = False
    df.to_csv('contacts.csv', index=False)
    get_info_contacts(browser, df) 
    
if __name__ == "__main__":
    starting_point = time.time()
    get_all_contacts()
    elapsed_time = round((time.time() - starting_point) / 60, 2)
    print("Tiempo total en minutos: " + str(elapsed_time))
