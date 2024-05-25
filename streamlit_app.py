import pandas as pd
import yaml
from yaml.loader import SafeLoader
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.exceptions import (CredentialsError,
                                                          LoginError,
                                                          RegisterError,
                                                          ResetError)

############################## LOGIN  ##############################################

def login(auth:stauth.Authenticate):
    # Creating a login widget
    try:
        auth.login(clear_on_submit=True)
    except LoginError as e:
        st.error(e)

    if st.session_state["authentication_status"]:   # Authentication successful
        return True
    elif st.session_state["authentication_status"] is False:    # Authentication failed
        st.error('Username/password is incorrect')

############################  LOGOUT  ##############################################

def create_logout_widget(auth:stauth.Authenticate):
    auth.logout(location='sidebar')

############################  RESET PASSWORD  ######################################

def create_reset_pw_widget(auth:stauth.Authenticate):
    try:
        if auth.reset_password(st.session_state["username"], location='sidebar'):
            st.success('Password modified successfully')
    except ResetError as e:
        st.error(e)
    except CredentialsError as e:
        st.error(e)
    except AttributeError as e:
        pass

############################  REGISTER USER  ######################################

def register_user(auth:stauth.Authenticate):
    try:
        (email_of_registered_user,
        username_of_registered_user,
        name_of_registered_user) = auth.register_user(pre_authorization=False, clear_on_submit=True)
        if email_of_registered_user:
            st.success('User registered successfully')
    except RegisterError as e:
        st.error(e)

############################## INVENTORY APP  ######################################

def inventory_app():
    # Display Title and Description
    st.title("Vendor Management Portal")
    st.markdown("Enter the details of the new vendor below.")

    # Establishing a Google Sheets connection
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Fetch existing vendors data
    existing_data = conn.read(worksheet="Inventario", usecols=list(range(6)), ttl=5)
    existing_data = existing_data.dropna(how="all")

    # List of Business Types and Products
    BUSINESS_TYPES = [
        "Manufacturer",
        "Distributor",
        "Wholesaler",
        "Retailer",
        "Service Provider",
    ]
    PRODUCTS = [
        "Electronics",
        "Apparel",
        "Groceries",
        "Software",
        "Other",
    ]

    # Onboarding New Vendor Form
    with st.form(key="vendor_form"):
        company_name = st.text_input(label="Company Name*")
        business_type = st.selectbox("Business Type*", options=BUSINESS_TYPES, index=None)
        products = st.multiselect("Products Offered", options=PRODUCTS)
        years_in_business = st.slider("Years in Business", 0, 50, 5)
        onboarding_date = st.date_input(label="Onboarding Date")
        additional_info = st.text_area(label="Additional Notes")

        # Mark mandatory fields
        st.markdown("**required*")

        submit_button = st.form_submit_button(label="Submit Vendor Details")

        # If the submit button is pressed
        if submit_button:
            # Check if all mandatory fields are filled
            if not company_name or not business_type:
                st.warning("Ensure all mandatory fields are filled.")
                st.stop()
            elif existing_data["CompanyName"].str.contains(company_name).any():
                st.warning("A vendor with this company name already exists.")
                st.stop()
            else:
                # Create a new row of vendor data
                vendor_data = pd.DataFrame(
                    [
                        {
                            "CompanyName": company_name,
                            "BusinessType": business_type,
                            "Products": ", ".join(products),
                            "YearsInBusiness": years_in_business,
                            "OnboardingDate": onboarding_date.strftime("%Y-%m-%d"),
                            "AdditionalInfo": additional_info,
                        }
                    ]
                )

                # Add the new vendor data to the existing data
                updated_df = pd.concat([existing_data, vendor_data], ignore_index=True)

                # Update Google Sheets with the new vendor data
                conn.update(worksheet="Inventario", data=updated_df)

                st.success("Vendor details successfully submitted!")

################################## MAIN APP  #######################################

def main_app(auth:stauth.Authenticate):
    create_logout_widget(auth=auth)
    create_reset_pw_widget(auth=auth)
    inventory_app()

############################################################################################

if __name__ == '__main__':
    # Loading config file
    with open('../config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.load(file, Loader=SafeLoader)

    # Creating the authenticator object
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    if login(auth=authenticator):
        main_app(auth=authenticator)
    
    # register_user(auth=authenticator)

    # Saving config file
    with open('../config.yaml', 'w', encoding='utf-8') as file:
        yaml.dump(config, file, default_flow_style=False)
