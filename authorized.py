import streamlit as st  
import database as db 
import datetime 
import pandas as pd 
import base64 
import time 
import binascii
import psycopg2

ROLES=['User']

def get_dataframe():
    conn=db.connect_db() 
    auth_users=db.fetch_data(conn,table_name='authorized_users',fetch_attributes='id,username,role,last_logged_in',data='all')
    users_df = pd.DataFrame(auth_users, columns=['UserID', 'username', 'Role', 'last_logged_in'],)
    return users_df

def auth_interface(user):
    try:
        st.write('<p style="color: blue; border-bottom: 1px solid white; margin-top: -50px; font-size: 30px; font-weight: bold">Criminova - Authorized Users</p>', unsafe_allow_html=True)
        conn=db.connect_db()
        system_admin=db.from_db(conn,f"select name,role,image,last_logged_in,email,contact from authorized_users where username='{user}'")
        # Fetch data for the authorized users dataframe
        data = get_dataframe() 
        
        # Split the page into two columns
        left_column, right_column = st.columns(2)
        
        # Right column: Options for update: To update the credential 
        with right_column.container(border=True):
            st.write('<p style="color: blue; border-bottom: 1px solid white; margin-top: 0px; font-size: 20px; font-weight: bold">Update Details</p>', unsafe_allow_html=True)
            email=st.text_input('Email',value=system_admin[4])
            contact=st.text_input('Contact',value=system_admin[5])
            
            if st.button('Update',use_container_width=True):
                placeholder=st.empty() 
                if email.strip():
                    conn=db.connect_db()
                    db.run_query(conn,f"Update authorized_users set email='{email}' where username='{user}'",placeholder,"Updated Successfully")
                if contact.strip():
                    conn=db.connect_db()
                    db.run_query(conn,f"Update authorized_users set contact='{contact}' where username='{user}'",placeholder,"Updated Successfully")
                time.sleep(3)
                placeholder.empty()
                st.rerun() 
        if system_admin[1] != 'Administrator':
            st.info('Contact Administrator for further')

    # Add New Users to the table 
        if system_admin[1]=='Administrator':
            with right_column.form("Add",border=True,clear_on_submit=True):
                st.write('<p style="color: blue; border-bottom: 1px solid white; margin-top: 0px; font-size: 20px; font-weight: bold">Add User</p>', unsafe_allow_html=True)
                name=st.text_input('Name',placeholder='Full Name',label_visibility='collapsed')
                username=st.text_input('User Name',placeholder='User Name',label_visibility='collapsed')
                key=st.text_input('Passkey',placeholder='Pass Key',label_visibility='collapsed',type='password')
                role=st.selectbox('Role',placeholder='Role',label_visibility='collapsed',options=ROLES,index=None)
                email=st.text_input('Email',placeholder='email',label_visibility='collapsed')
                contact=st.text_input('Contact',placeholder='contact',label_visibility='collapsed')
                image=st.file_uploader('Image',type=['jpg','jpeg','png'])
                if st.form_submit_button('Add User',use_container_width=True):
                    placeholder=st.empty() 
                    if name.strip() and username.strip() and key.strip() and role.strip() and email.strip() and contact.strip and image:
                        password=db.hash_generator(key)
                        hashed=binascii.hexlify(password).decode('utf-8')
                        image=image.read() 
                        conn=db.connect_db() 
                        db.run_query(conn,f"""
                                        insert into authorized_users(name,username,role,password,email,contact,image)
                                        values('{name}','{username.strip()}','{role}','{hashed}','{email}','{contact}',{psycopg2.Binary(image)})
                                    """,placeholder,"Added Successfully")
                    else:   
                        placeholder.error('All Fields Required')
                    time.sleep(3)
                    placeholder.empty() 
                    st.rerun() 

                
        # Left column: Details of the system administrator
        with left_column.container(border=True):
            st.write(
                f"""
                    <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; height: 100%;'>
                    <img src="data:image/png;base64,{base64.b64encode(system_admin[2]).decode()}"  width="150" height="150" style="margin-bottom: 10px; border-radius: 50%; object-fit: cover;" />
                    <p style='margin-bottom: 5px; font-size: 20px; font-weight: bold;'>{system_admin[1]}</p>
                    <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Name:</b> {system_admin[0]}</p>
                    <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Username:</b> {user}</p>
                    <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>email:</b> {system_admin[4]}</p>
                    <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Contact:</b> {system_admin[5]}</p>
                    <p style='margin-bottom: 2px; font-size: 16px; color:grey;'><b>Last Logged In:</b> {system_admin[3]}</p>
                    <p>  </p>
                    
                </div>
                """,
                unsafe_allow_html=True
            )
            if system_admin[1] == 'Administrator':
                c1,c2,c3=st.columns([1,2,1])
                with c2.popover('Handover',use_container_width=True):
                    conn=db.connect_db()
                    db_users=db.get_all(conn,"select username from authorized_users where role != 'Administrator'")
                    if db_users:    
                        opt=[users[0] for users in db_users]
                        to_user=st.selectbox('Assign Administrator',options=opt,index=None,placeholder='Select Administrator')
                        state=st.radio('Assign',['Assign Only','Assign and Leave'],label_visibility='collapsed')
                        placeholder=st.empty() 
                        if st.button(state,use_container_width=True):
                            if to_user:
                                conn=db.connect_db() 
                                if state=='Assign Only':
                                    db.run_query(conn,f"""
                                                    update authorized_users set role='Administrator' where username='{to_user}';
                                                    update authorized_users set role='User' where username='{user}';
                                                """,placeholder,"Updated Successfully")
                                else:
                                    db.run_query(conn,f"""
                                                    update authorized_users set role='Administrator' where username='{to_user}';
                                                    delete from authorized_users where username='{user}';
                                                """,placeholder,"Updated Successfully")
                                    st.session_state.logged_in=False 
                                time.sleep(3)
                                placeholder.empty() 
                                st.rerun()  
                            else:
                                placeholder.error('No user selected.')

        if system_admin[1]=='Administrator':
            with left_column.container(border=True):
                st.write('<p style="color: blue; border-bottom: 1px solid white; margin-top: 0px; font-size: 20px; font-weight: bold">Remove User</p>', unsafe_allow_html=True)
                conn=db.connect_db()
                db_users=db.get_all(conn,"select username from authorized_users where role != 'Administrator'")
                if db_users:    
                    remove_opt=[users[0] for users in db_users]
                    to_remove=st.selectbox('UserName',placeholder='Select User to remove',options=remove_opt)
                    placeholder=st.empty() 
                    if st.button('Remove',use_container_width=True):
                        conn=db.connect_db()
                        db.run_query(conn,f"delete from authorized_users where username='{to_remove}'",placeholder,msg='Removed Successfully')
                        time.sleep(3)
                        placeholder.empty() 
                        st.rerun() 
                else:
                    st.write('No Users available')
            

            # Display the authorized users dataframe
            left_column.write('<p style="color: white; border-bottom: 1px solid white; margin-top: 0px; font-size: 20px; font-weight: bold">User Logs</p>', unsafe_allow_html=True)
            left_column.dataframe(data, hide_index=True,use_container_width=True,height=200)
    except Exception as e:
        st.error(f'Something Wrong with database: {e}')

if __name__=='__main__':
    auth_interface('jay') 