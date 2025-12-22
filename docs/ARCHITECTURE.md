# ARCHITECTURAL DECISIONS

<h2>News Scraping</h2>

- **Gmail Newsletters:** For scraping Gmail newsletters, we use a tool that relies on Gmail's API and on BeautifulSoup to extract relevant news, which are output in JSON format ready for database injection.

- **Tavily (for database):** In addition to the Gmail newsletters, we implemented news scraping from entrepreneurship-related websites using Tavily's API, and its output would then be formatted according to our needs. In a first stage of the project, this seemed to be the most viable option out of other similar ones. However, we noticed that Tavily was extracting too much "noise" (homepages, cookie banners, "About Us" pages,...) and struggling to meet given requirements, namely the news timeframe that we gave it. Even after fine-tuning existing parameters and testing with new ones, we still did not manage to get the platform working as intended, and this also influenced the RAG results (for example, the results obtained in the Chat were much worse than they were supposed to). Consequently, this was ultimately scrapped from our project.

- **Tavily (for single website scraping):** Nonetheless, Tavily still proved useful for scraping one website at a time, in the Chat section of deNoise. The approach is the same, however the answer is given by the built-in Tavily LLM instead of Gemini. We assume that it is better suited to deal with the generated "noise" mentioned above, however we were not able to understand clearly what worked differently here.


<h2>Frameworks</h2>

As our main framework, we chose LangChain since it includes essential modules that allow interactions between the LLM and the database.

In addition to this, some other libraries were used, namely azure-cosmos, google-genai, pandas, python-dotenv and some others for specific tasks.


<h2>Database Implementation</h2>

The database where news articles are saved is an Azure CosmosDB implementation. Three containers exist:

- **newsArticles:** Actual news articles are stored here in JSON format, with the fields `id`, `title`, `text` and `data`.

- **newsEmbeddings:** Embedded news are stored here and are the ones that enable similarity search. In addition, non-embedded content of the NewsDB container also exist here.

- **userProfiles:** User information obtained from Lovable's frontend is stored in this container.

Azure CosmosDB was chosen because it integrates smoothly with the rest of the project's stack, it has a powerful vector search (essential for RAG operations), also benefits from a generous free tier.


<h2>Agents</h2>

- **LLM:** The LLM we use to generate content for this project is Google's Gemini 2.5 Flash. It was chosen mainly because it is the one that we explored in more detail in class, but also because it is powerful and has generous usage limits.

- **Text-to-Speech (for the Podcast):** We used ElevenLabs to perform the text-to-speech conversion of deNoise's Podcast function. Again, it was a platform that we had already used before and knew it was capable of doing what we intended. A Creator Plan subscription was needed for interaction with Render, as the free tier did not allow this (even if credits were enough).


<h2>Frontend</h2>

The frontend for our project is done using Lovable, and is separated into Home and three other pages: Chat, Report and Podcast, which generate a distinct response according to the user's choice and needs. The user may also choose to sign in and define custom instructions which are fed into all agents.
Lovable was chosen as it was a platform we were already familiar with and allowed a relatively straightforward implementation of the project, without any major issues.


<h2>Deployment Platform</h2>

We used Render as our deployment platform. Given the use of multiple external services and APIs, including Azure CosmosDB, Google Gemini, ElevenLabs, and Lovable, Render’s managed infrastructure and opinionated defaults reduced deployment friction and configuration risk. This allowed us to focus on architectural and functional decisions rather than infrastructure management, which would have offered limited marginal value given the project’s scale and performance requirements. In this setting, Render represents a deliberate trade-off in favour of reliability, simplicity, and development speed over granular control.