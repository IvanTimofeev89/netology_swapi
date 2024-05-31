import asyncio
from datetime import datetime

import aiohttp

from models import init_db, Session, SwapiPeople
from more_itertools import chunked

MAX_CHUNK = 10


async def get_response(path, session):
    async with session.get(path) as response:
        json_data = await response.json()
        return json_data


async def get_lists(list_of_links, field_name, http_session):
    coros = [get_response(link, http_session) for link in list_of_links]
    result = await asyncio.gather(*coros)
    objects_array = [elem.get(f"{field_name}") for elem in result]

    return objects_array


async def prepare_orm_obj(person, http_session):
    tasks = []

    films_task = None
    if person.get("films"):
        films_task = asyncio.create_task(
            get_lists(person["films"], "title", http_session)
        )
        tasks.append(films_task)

    species_task = None
    if person.get("species"):
        species_task = asyncio.create_task(
            get_lists(person["species"], "name", http_session)
        )
        tasks.append(species_task)

    starships_task = None
    if person.get("starships"):
        starships_task = asyncio.create_task(
            get_lists(person["starships"], "name", http_session)
        )
        tasks.append(starships_task)

    vehicles_task = None
    if person.get("vehicles"):
        vehicles_task = asyncio.create_task(
            get_lists(person["vehicles"], "name", http_session)
        )
        tasks.append(vehicles_task)

    await asyncio.gather(*tasks)

    films_list = films_task.result() if films_task else []
    species_list = species_task.result() if species_task else []
    starships_list = starships_task.result() if starships_task else []
    vehicles_list = vehicles_task.result() if vehicles_task else []

    orm_object = SwapiPeople(
        birth_year=person.get("birth_year", "n/a"),
        eye_color=person.get("eye_color", "n/a"),
        films=",".join(films_list),
        gender=person.get("gender", "n/a"),
        hair_color=person.get("hair_color", "n/a"),
        height=person.get("height", "n/a"),
        homeworld=person.get("homeworld", "n/a"),
        mass=person.get("mass", "n/a"),
        name=person.get("name", "n/a"),
        skin_color=person.get("skin_color", "n/a"),
        species=",".join(species_list),
        starships=",".join(starships_list),
        vehicles=",".join(vehicles_list),
    )
    return orm_object


async def insert_to_db(list_of_people, http_session):
    async with Session() as session:
        person_coros = [
            prepare_orm_obj(person, http_session) for person in list_of_people
        ]
        orm_obj_list = await asyncio.gather(*person_coros)
        session.add_all(orm_obj_list)
        await session.commit()


async def main(base_path):
    await init_db()
    async with aiohttp.ClientSession() as http_session:
        api_response = await get_response(base_path, http_session)
        people_count = api_response["count"]
        people_ids = chunked(range(1, people_count + 1), MAX_CHUNK)
        for people_ids_chunk in people_ids:
            coros = [
                get_response(f"{base_path}/{people_id}/", http_session)
                for people_id in people_ids_chunk
            ]
            list_of_people = await asyncio.gather(*coros)
            asyncio.create_task(insert_to_db(list_of_people, http_session))

        main_task = asyncio.current_task()
        current_tasks = asyncio.all_tasks()
        current_tasks.remove(main_task)
        await asyncio.gather(*current_tasks)


BASE_PATH = "https://swapi.dev/api/people"
start = datetime.now()
asyncio.run(main(BASE_PATH))
print(datetime.now() - start)
print("Finished")
