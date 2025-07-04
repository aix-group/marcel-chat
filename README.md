<p align="center">
  <img height="150px" src="docs/tagline.svg">
</p>

---

Marcel is a lightweight, open-source conversational agent designed to support prospective students with admission-related inquiries. It aims to provide fast and personalized responses while reducing the workload of university support staff. The system is engineered for easy deployment in resource-constrained academic settings.

**More information:** [Paper]() | [Demo video]()

## Quickstart

### Clone repository

```sh
git clone git@github.com:aix-group/marcel-chat.git
```

### Configure environment

Create a `.env` file based on the template and set the required variables.

```sh
cp .env.example .env
vi .env # Please refer to the .env file for configuration options
```
### Data
Simplified data is available in the [data folder](./data/)

The **FAQ** must be a well-formatted ```.json``` file. Each entry should include the following keys: ```id```, ```question```, and ```sources```.
<details>
<summary> <b>FAQ Example</b> </summary>

```json
[
  {
        "id": "faq-0001",
        "question": "Does the Master Data Science have a minimum grade requirement?",
        "sources": [
            "https://www.uni-marburg.de/en/studying/after-your-first-degree/masters-programs/degree-programs/datasciencems",
            "https://www.uni-marburg.de/en/studying/after-your-first-degree/masters-programs/application-for-a-masters-programme/eap/eap-data-science"
        ]
    }
]
```

</details>
<br>

The **knowledge base** must be a well-formatted ```.jsonl``` file. Each entry should contain the following keys: ```url```, ```content```, ```favicon```, and ```og```(can be empty dict).
<details>
<summary><b>Knowledge base Example</b></summary>

```json
{"url": "https://www.uni-marburg.de/en/studying/after-your-first-degree/masters-programs/application-for-a-masters-programme/master", "content": "# Master\n\n  \n\n\n\n\n", "og": {"og:site_name": "Philipps-Universit\u00e4t Marburg", "og:title": "Master", "og:type": "website", "og:description": "", "og:url": "https://www.uni-marburg.de/en/studying/after-your-first-degree/masters-programs/application-for-a-masters-programme/master", "og:image": "https://www.uni-marburg.de/@@site-logo/favicon.ico", "og:image:type": "image/x-icon"}, "favicon": "https://www.uni-marburg.de/++theme++plonetheme.unimr/layout/favicon.ico"}
```

</details>
<br>

Plese refer [backend instruction](./backend/README.md) for ```admins``` configuration
<details>
<summary><b>Admins Example</b></summary>

```json
[
    {
        "username": "admin",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$FRnc99KQkJkRK+1RkTueyg$WbJ64c5iyXgHDy3nJyGqpEAyc1VsM8Q63ocF4XMRTF8"
    }
]

```
</details>


### Generate certificates

The application supports HTTPs-encrypted traffic. For development purposes, you can generate certificates like this:

```sh
mkdir certs
cd certs
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout selfsigned.key \
  -out  selfsigned.crt \
  -subj "/CN=localhost"
sudo chmod +r selfsigned.crt
sudo chmod +r selfsigned.key
```

### Start Containers
```sh
docker compose --env-file .env up
```
The app will be available at: https://localhost:8080/

## Development instructions
Refer to the following documents:

- [Backend](./backend/README.md)
- [Frontend](./frontend/README.md)
- [Scraper](./scraper/README.md)
- **Docker Deployment:** [Docker](./docs/docker.md)
