from langchain_community.document_loaders import YoutubeLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAI
from langchain.chains.summarize import load_summarize_chain
from vertexai.generative_models import GenerativeModel
from langchain.prompts import PromptTemplate
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class GeminiProcessor:
    def __init__(self, model_name, project):
        self.model = VertexAI(model_name=model_name, project=project)

    def generate_document_summary(self, documents:list, **args):

        chain_type = "map_reduce" if len(documents) >10 else "stuff"

        chain = load_summarize_chain(
            llm = self.model,
            chain_type=chain_type,
            **args
        )

        return chain.run(documents)

    def count_total_token(self, docs:list):
        """
        Maintains a progress bar for tokens counted
        """
        temp_model = GenerativeModel("gemini-1.0-pro")
        total = 0
        logger.info("Counting total billable characters..")
        for doc in tqdm(docs):
            total += temp_model.count_tokens(doc.page_content).total_billable_characters
        
        return total


        

    def get_model(self):
        return self.model

class YoutubeProcessor:

    #Retrieve transcript

    def __init__(self, genai_processor:GeminiProcessor):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap = 0
        )

        self.GeminiProcessor = genai_processor

    def retrieve_youtube_documents(self, video_url:str, verbose=False):

        loader = YoutubeLoader.from_youtube_url(video_url,
                 add_video_info = True)
        result = loader.load()
        result = self.text_splitter.split_documents(result)

        author = result[0].metadata['author']
        length = result[0].metadata['length']
        title = result[0].metadata['title']
        total_size = len(result)
        total_billable_characters = self.GeminiProcessor.count_total_token(result)
        if verbose:
            logger.info(f"{author}\n{length}\n{title}\n{total_size}")

        return result
    
    def find_key_concepts(self, documents:list, group_size:int=2):
        
        if group_size > len(documents):
            raise ValueError("group size cannot be greate than document length")
        
        #Find number of documents per group

        docs_per_group = len(documents) // group_size + (len(documents) % group_size >0)

        #Split the doc in chunks of size doc_per_group

        groups = [documents[i:i+docs_per_group] for i in range(0,len(documents), docs_per_group)]

        batch_concepts = []

        logger.info("Finding the key concepts")

        for group in tqdm(groups):
            #Combine contebt of documents per group
            """
            1)grabbing per group
            2)get number of docs per group
            3)Add all strings
            4)Inject into prompt

            """
            group_content = ""

            for doc in group:
                group_content+=doc.page_content

            #Prompt for finding key concepts

            prompt = PromptTemplate(
                template="""
                Find and define key concepts or terms found in the text:
                {text}

                Respond in the following format as a string separating each concept with a comma:
                "concept":"definition"
                """,
                input_variables= ["text"]

            )

            #Creating chain
            chain = prompt | self.GeminiProcessor.model

            #Run chain
            # Invoking this completes prompt using group_content and sends the prompt to GeminiProcess model
            # Concept stores the output of the model 
            concept = chain.invoke({"text": group_content}) 
            batch_concepts.append(concept)

        return batch_concepts
            


    

        
    
        

