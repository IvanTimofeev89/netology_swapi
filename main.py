import asyncio
import aiohttp

from models import init_db, Session, SwapiPeople


async def get_response(path, session):
    async with session.get(path) as response:
        json_data = await response.json()
        return json_data

async def insert_to_db(list_of_people):
    async with Session() as session:
        orm_objects = [SwapiPeople(
            birth_year=person['birth_year'],
            eye_color=person['eye_color'],
            films=','.join(person['films']),
            gender=person['gender'],
            hair_color=person['hair_color'],
            height=person['height'],
            homeworld=person['homeworld'],
            mass=person['mass'],
            name=person['name'],
            skin_color=person['skin_color'],
            species=','.join(person['species']),
            starships=','.join(person['starships']),
            vehicles=','.join(person['vehicles'])
        ) for person in list_of_people]
        session.add_all(orm_objects)
        await session.commit()

async def main(path):
    async with aiohttp.ClientSession() as session:
        api_response = await get_response(path, session)
        people = api_response['results']
        await insert_to_db(people)

        next_page_path = api_response.get('next')
        if next_page_path:
            await main(next_page_path)



BASE_PATH = 'https://swapi.dev/api/people'
asyncio.run(init_db())
asyncio.run(main(BASE_PATH))
print("Finished")