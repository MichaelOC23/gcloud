

import time
import streamlit as st
from typing import Literal
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import jwt
from jwt import DecodeError, InvalidSignatureError
import streamlit as st
import extra_streamlit_components as stx


class Authenticate:
    def __init__(self, secret_credentials_path:str, redirect_uri: str, cookie_name: str, cookie_key: str, cookie_expiry_days: float=30.0):
        st.session_state['IS_AUTHENTICATED_TO_GOOGLE']   =   st.session_state.get('IS_AUTHENTICATED_TO_GOOGLE', False)
        self.secret_credentials_path    =   secret_credentials_path
        self.redirect_uri               =   redirect_uri
        self.cookie_handler             =   CookieHandler(cookie_name,
                                                          cookie_key,
                                                          cookie_expiry_days)

    def get_authorization_url(self) -> str:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            self.secret_credentials_path, # replace with you json credentials from your google auth app
            scopes=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
            redirect_uri=self.redirect_uri,
        )

        authorization_url, state = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
            )
        return authorization_url

    def login(self, color:Literal['white', 'blue']='blue', justify_content: str="center", cred_dict={}) -> tuple:
        self.secret_credentials_path = cred_dict
        if not st.session_state['IS_AUTHENTICATED_TO_GOOGLE']:
            flow = google_auth_oauthlib.flow.Flow.from_client_config(
                self.secret_credentials_path, # replace with you json credentials from your google auth app
                scopes=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
                redirect_uri=self.redirect_uri,
            )

            authorization_url, state = flow.authorization_url(
                    access_type="offline",
                    include_granted_scopes="true",
                )
            
            html_content = f"""
            <div style="display: flex; justify-content: {justify_content};">
                <a href="{authorization_url}" target="_self" style="background-color: {'#fff' if color == 'white' else '#4285f4'}; color: {'#000' if color == 'white' else '#fff'}; text-decoration: none; text-align: center; font-size: 16px; margin: 4px 2px; cursor: pointer; padding: 8px 12px; border-radius: 4px; display: flex; align-items: center;">
                    <img src="https://lh3.googleusercontent.com/COxitqgJr1sJnIDe8-jiKhxDx1FrYbtRHKJ9z_hELisAlapwE9LUPh6fcXIfb5vwpbMl4xl9H9TRFPc5NOO8Sb3VSgIBrfRYvW6cUA" alt="Google logo" style="margin-right: 8px; width: 26px; height: 26px; background-color: white; border: 2px solid white; border-radius: 4px;">
                    Sign in with Google
                </a>
            </div>
            """

            st.markdown(html_content, unsafe_allow_html=True)

    def confirm_google_authentication(self):
        if not st.session_state['IS_AUTHENTICATED_TO_GOOGLE']:
            print('User is not authenticated')
            token = self.cookie_handler.get_cookie()
            if token:
                print ('Found token/cookie, using it to authenticate')
                user_info = {
                    'name': token['name'],
                    'email': token['email'],
                    'picture': token['picture'],
                    'id': token['oauth_id']
                }
                st.query_params.clear()
                st.session_state["IS_AUTHENTICATED_TO_GOOGLE"] = True
                st.session_state["user_info"] = user_info
                st.session_state["oauth_id"] = user_info.get("id")
                return True
            else:
                print('No token found, redirecting to Google')


            time.sleep(0.3)
            
            if not st.session_state['IS_AUTHENTICATED_TO_GOOGLE']:
                auth_code = st.query_params.get("code")
                st.query_params.clear()
                if auth_code:
                    print ('Received auth code: {}'.format(auth_code))
                    flow = google_auth_oauthlib.flow.Flow.from_client_config (
                        self.secret_credentials_path, # replace with you json credentials from your google auth app
                        scopes=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"],
                        redirect_uri=self.redirect_uri,
                    )
                    flow.fetch_token(code=auth_code)
                    credentials = flow.credentials
                    user_info_service = build(
                        serviceName="oauth2",
                        version="v2",
                        credentials=credentials,
                    )
                    user_info = user_info_service.userinfo().get().execute()
                    print (f'Successfully authenticated user: {user_info}')

                    st.session_state["IS_AUTHENTICATED_TO_GOOGLE"] = True
                    st.session_state["oauth_id"] = user_info.get("id")
                    st.session_state["user_info"] = user_info
                    self.cookie_handler.set_cookie(user_info.get("name"), user_info.get("email"), user_info.get("picture"), user_info.get("id"))
                    st.rerun()
        else:
            return True

    def logout(self):
        st.session_state['logout'] = True
        st.session_state['name'] = None
        st.session_state['username'] = None
        st.session_state['IS_AUTHENTICATED_TO_GOOGLE'] = None
        self.cookie_handler.delete_cookie()





class CookieHandler:
    def __init__(self, cookie_name: str, cookie_key: str, cookie_expiry_days: float=30.0):
        """
        Create a new instance of "CookieHandler".

        Parameters
        ----------
        cookie_name: str
            Name of the cookie stored on the client's browser for password-less re-authentication.
        cookie_key: str
            Key to be used to hash the signature of the re-authentication cookie.
        cookie_expiry_days: float
            Number of days before the re-authentication cookie automatically expires on the client's
            browser.
        """
        self.cookie_name            =   cookie_name
        self.cookie_key             =   cookie_key
        self.cookie_expiry_days     =   cookie_expiry_days
        self.cookie_manager         =   stx.CookieManager()
        self.token                  =   None
        self.exp_date               =   None

    def get_cookie(self) -> str:
        """
        Retrieves, checks, and then returns the re-authentication cookie.

        Returns
        -------
        str
            re-authentication cookie.
        """
        if 'logout' in st.session_state and st.session_state['logout']:
            return False
        self.token = self.cookie_manager.get(self.cookie_name)
        if self.token is not None:
            self.token = self._token_decode()
            if (self.token is not False and 'email' in self.token.keys() and
                self.token['exp_date'] > datetime.now().timestamp()):
                return self.token

    def delete_cookie(self):
        """
        Deletes the re-authentication cookie.
        """
        try:
            self.cookie_manager.delete(self.cookie_name)
        except KeyError as e:
            print(e)

    def set_cookie(self, name, email, picture, oauth_id):
        """
        Sets the re-authentication cookie.
        """
        self.exp_date = self._set_exp_date()
        token = self._token_encode(name, email, picture, oauth_id)
        self.cookie_manager.set(self.cookie_name, token,
                                expires_at=datetime.now() + timedelta(days=self.cookie_expiry_days))

    def _set_exp_date(self) -> str:
        """
        Sets the re-authentication cookie's expiry date.

        Returns
        -------
        str
            re-authentication cookie's expiry timestamp in Unix Epoch.
        """
        return (datetime.now() + timedelta(days=self.cookie_expiry_days)).timestamp()

    def _token_decode(self) -> str:
        """
        Decodes the contents of the re-authentication cookie.

        Returns
        -------
        str
            Decoded cookie used for password-less re-authentication.
        """
        try:
            return jwt.decode(self.token, self.cookie_key, algorithms=['HS256'])
        except InvalidSignatureError as e:
            print(e)
            return False
        except DecodeError as e:
            print(e)
            return False

    def _token_encode(self, name : str, email: str, picture: str, oauth_id: str) -> str:
        """
        Encodes the contents of the re-authentication cookie.

        Returns
        -------
        str
            Cookie used for password-less re-authentication.
        """
        return jwt.encode({'email': email, 'name': name, 'picture': picture, 'oauth_id': oauth_id,
            'exp_date': self.exp_date}, self.cookie_key, algorithm='HS256')

