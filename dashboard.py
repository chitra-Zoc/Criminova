import plotly.express as px
import pandas as pd
import database as db
import streamlit as st

def hot_cases():
    conn = db.connect_db() 
    hot_cases = db.get_all(conn, """
                     SELECT nature_of_case, case_count FROM nature_of_case WHERE case_count > 0
                     """)
    try:
        cases_df = pd.DataFrame(hot_cases, columns=['Nature of Case', 'Case Count'])
        # Create a Plotly bar chart
        fig = px.bar(cases_df, x='Case Count', y='Nature of Case', orientation='h', 
                    # title='Hot Cases by Nature', 
                    labels={'Nature of Case': 'Nature of Case'},
                    width=500, height=300, 
                    hover_name='Nature of Case',
                    hover_data='Case Count',
                    barmode='overlay', # Group bars together
                    color_discrete_sequence=['#000AEB'], # Set bar color
                    )    
        st.plotly_chart(fig,use_container_width=True)
    except Exception:
        st.error('Something went wrong')

# Load daily new cases data
def daily_cases():
    conn=db.connect_db() 
    daily_new_cases=db.get_all(conn,"""SELECT case_date AS Date, COUNT(*) AS New_Cases
                                        FROM caseReports
                                        GROUP BY case_date
                                        ORDER BY case_date;
                                    """)
    try:
        dataframe=pd.DataFrame(daily_new_cases,columns=['Date','Case Count'])
        # Create a line chart using Plotly Express
        fig = px.line(dataframe, x=dataframe['Date'], y=dataframe['Case Count'], 
                    #   title='Daily New Cases', 
                      labels={'Date': 'Date', 'New Cases': 'New Cases'},
                      width=800, height=400)
        
        # Display the line chart
        st.plotly_chart(fig,use_container_width=True)
    except Exception as e:
        st.error('Something went wrong')

def combined_gender_chart():
    conn=db.connect_db() 
    # Get data for victims by gender
    victim_by_gender=db.get_all(conn,"""
                        SELECT gender AS Gender, COUNT(*) AS Total_Cases FROM victims
                        GROUP BY gender
                        ORDER BY gender
                            """)
    # Get data for suspects by gender
    conn=db.connect_db() 
    suspects_by_gender=db.get_all(conn,"""
                        SELECT gender AS Gender, COUNT(*) AS Total_Cases FROM suspects
                        GROUP BY gender
                        ORDER BY gender
                            """)
    try:
        # Convert the query results to DataFrames
        victims_df = pd.DataFrame(victim_by_gender, columns=['Gender', 'Total_Cases'])
        victims_df['Gender'] = victims_df['Gender'].fillna('Unidentified')
        victims_df['Gender'] = victims_df['Gender'].replace('None', 'Unidentified')
        victims_df = victims_df.groupby('Gender', as_index=False).sum()
        suspects_df = pd.DataFrame(suspects_by_gender, columns=['Gender', 'Total_Cases'])
        suspects_df['Gender'] = suspects_df['Gender'].fillna('Unidentified')
        suspects_df['Gender'] = suspects_df['Gender'].replace('None', 'Unidentified')
        suspects_df = suspects_df.groupby('Gender', as_index=False).sum()
        
        # Merge the DataFrames
        combined_df = pd.merge(victims_df, suspects_df, on='Gender', suffixes=('_Victims', '_Suspects'), how='outer')
        combined_df['Gender'] = combined_df['Gender'].fillna('Unidentified')
        combined_df = combined_df.groupby('Gender', as_index=False).sum()

        # Create a combined clustered bar chart using Plotly Express
        fig = px.bar(combined_df, x='Gender', y=['Total_Cases_Victims', 'Total_Cases_Suspects'], 
                    #  title='Combined Victims and Suspects by Gender', 
                     labels={'Gender': 'Gender', 'value': 'Total Cases'},
                     width=800, height=400,
                     color_discrete_map={'Total_Cases_Victims': 'blue', 'Total_Cases_Suspects': 'orange'},
                     barmode='group',
                     )
        
        # Display the combined clustered bar chart
        st.plotly_chart(fig,use_container_width=True)
    except Exception as e:
        st.error('Something went wrong:')


# Display line chart for daily new cases
def main():
    st.write('<p style="color: blue; border-bottom: 1px solid white; margin-top: -50px; font-size: 30px; font-weight: bold">Criminova - Dashboard</p>', unsafe_allow_html=True)
    with st.container(border=True):
        st.write('<p style="color: grey; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Daily Cases Trend</p>', unsafe_allow_html=True)
        daily_cases()
    with st.container(border=True):
        st.write('<p style="color: grey; border-bottom: 1px solid white;font-size: 20px; font-weight: bold">Reported Cases</p>', unsafe_allow_html=True)
        hot_cases() 
    with st.container(border=True):
        st.write('<p style="color: grey; border-bottom: 1px solid white; font-size: 20px; font-weight: bold">Victims and Suspects by Gender</p>', unsafe_allow_html=True)
        combined_gender_chart()


if __name__=="__main__":
    main() 

