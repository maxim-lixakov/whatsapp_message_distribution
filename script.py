import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from time import sleep

def float_to_phone(number):
    if pd.isna(number):
        return None
    number_str = '{:.0f}'.format(number)
    return number_str if len(number_str) == 11 else None

def read_processed_contacts():
    sent_contacts = set()
    failed_contacts = set()
    try:
        with open('broadcast_results.txt', 'r') as file:
            for line in file:
                if "Message sent to: " in line:
                    contact = line.strip().split("Message sent to: ")[-1]
                    sent_contacts.add(contact)
                elif "Sorry message could not sent to " in line:
                    contact = line.strip().split("Sorry message could not sent to ")[-1]
                    failed_contacts.add(contact)
    except FileNotFoundError:
        print("broadcast_results.txt not found. Starting fresh.")
    return sent_contacts, failed_contacts

sent_contacts, failed_contacts = read_processed_contacts()
processed_contacts = sent_contacts.union(failed_contacts)
print(f"{len(processed_contacts)} contacts already processed.")

df = pd.read_excel('phones_rovercar.xlsx')
phones = df['Телефон'].apply(float_to_phone).tolist() + df['Мобильный телефон'].apply(float_to_phone).tolist()
filtered_phone_numbers = set(filter(None, phones))

contacts_to_process = filtered_phone_numbers - processed_contacts
print(f"Processing {len(contacts_to_process)} new contacts.")

df['Сообщение Отправлено'] = "нет"  # Default to "нет"

for index, row in df.iterrows():
    phone = float_to_phone(row['Телефон'])
    mobile_phone = float_to_phone(row['Мобильный телефон'])
    if phone in sent_contacts or mobile_phone in sent_contacts:
        df.at[index, 'Сообщение Отправлено'] = "да"
    elif phone in failed_contacts or mobile_phone in failed_contacts:
        df.at[index, 'Сообщение Отправлено'] = "нет"


df.to_excel('updated_phones_rovercar.xlsx', index=False)

chrome_options = Options()
# Add any specific options you might need
# chrome_options.add_argument("--headless")  # Example: running Chrome in headless mode

driver = webdriver.Chrome(options=chrome_options)
driver.get('https://web.whatsapp.com')
input("Press ENTER after login into Whatsapp Web and your chats are visiable.")

def create_broadcast_message():
    message = "🚚 Официальное сообщение от РОВЕРКАР 🚚\n                            Уважаемые клиенты, мы рады сообщить вам, что наш сервис переехал на новый адрес! Теперь мы находимся по адресу: 📍 Михайловский проезд, 4 стр 3. Это изменение позволит нам предложить вам ещё более качественный сервис и удобство обслуживания.\n                            Пожалуйста, обратите внимание, что номера телефонов остались прежними 📞. Мы всегда рады вашему звонку!\n                            Благодарим за ваше доверие и надеемся видеть вас на новом месте!"
    return message

message = create_broadcast_message()

# Add a message limit
message_limit = int(input("Enter the message limit: "))
messages_sent = 0

with open('broadcast_results.txt', 'a') as result_file:
    for contact in contacts_to_process:
        if messages_sent >= message_limit:
            print(f"Reached the message limit of {message_limit}. Stopping.")
            break
        try:
            url = 'https://web.whatsapp.com/send?phone={}&text={}'.format(contact, message)
            driver.get(url)
            try:
                click_btn = WebDriverWait(driver, 35).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, '_3XKXx')))
            except Exception as e:
                result_file.write(f"Sorry message could not sent to {contact}\n")
            else:
                sleep(2)
                click_btn.click()
                sleep(5)
                result_file.write(f'Message sent to: {contact}\n')
                messages_sent += 1
            result_file.flush()  # Flush after each write
        except Exception as e:
            result_file.write(f'Failed to send message to {contact} {e}\n')
            result_file.flush()  # Flush after each write
driver.quit()
result_file.write("The script executed successfully.\n")
result_file.flush()  # Final flush

print(f"Script executed successfully. {messages_sent} messages attempted.")
