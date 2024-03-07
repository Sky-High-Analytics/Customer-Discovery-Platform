## Customer Discovery Platform
This tool enables startups and marketing teams to gain insight from customer discovery and 
user interviews without pouring over hundreds of documents. It does so through the use of 
Retreival Augmented Generation (RAG), which searches through relevant documents and uses 
them as context for a large language model. Besides connecting to a local directory, the 
platform also connects to a Goodle Drive directory. Including this capability came out of 
a course I took at the University of Chicago Booth School of Business in which my team and I 
conducted a lot of customer discovery and uploaded our documents to a Google Drive folder.

## Running the Customer Discovery Platform
Unfortunately, due to privacy issues, getting the app up and running is a bit difficult. 
First, you should install the dependencies from the top-level diretory by running poetry 
init from a poetry environment. Then, create a .env file with your OpenAI API key. Next, you 
will need to configure a Google project on Google Cloud, create a service account in that 
project, enable the Sheets API, create and download Application Default Credentials, rename 
them to 'key.json', and store them in .credentials within the top-level directory. Finally, 
to get the app up and running in a browser, you should run 
flask --app customer_discovery_platform/backend run -p 8095 from a terminal and then 
streamlit run app.py from another terminal.

## Next Steps
A big issue with LLMs in most business settings is privacy. To deal with this for other 
projects, the next step will be replacing the OpenAI API calls with calls to an open source 
model, such as Mixtral 8X7B. However, this is difficult as there are many dependencies, the 
models is large, and speed is an issue.