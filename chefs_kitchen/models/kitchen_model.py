import logging
import math
import os
import time
from typing import List

from chefs_kitchen.models.chef_model import Chef
from chefs_kitchen.utils.logger import configure_logger
from chefs_kitchen.utils.api_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)

class KitchenModel:
    """ A class that represents a kitchen that can 
    """
    def __init__(self):
        self.kitchen: List[int] = []
        self._chefs_cache: dict[int, Chef] = []
        self._ttl: dict[int, float] = []
        self.ttl_seconds = int(os.getenv("TTL", 60))
        self.cuisines = ['Italian', 
                         'Chinese', 
                         'Greek', 
                         'Japanese', 
                         'Korean', 
                         'Indian', 
                         'Mexican',
                         'Cajun']
        
    def cookoff(self, cuisine: str):
        if len(self.kitchen) < 2: 
            logger.error("There must be at least two chefs to start a cookoff.")
            raise ValueError("There must be at least two chefs to start a cookoff.")

        skills_dict: dict[Chef, int] = []
        chefs = self.get_chefs
        
        logger.info("Chefs retrieved. Let the cookoff begin.")
        total_skill = 0
        for c in chefs:
            skill = self.calculate_chef_skill(c, cuisine)
            total_skill += skill
            skills_dict[c] = skill
            logger.info(f"Cooking skill for {c.name}: {skill:.3f}")
            
        r = get_random()
        logger.info(f"Random number retreived: {r:.3f}")
        progress = 0
        
        for chef in skills_dict:
            progress += skills_dict[chef] / total_skill
            if r < progress:
                winner = chef
                break
            
        logger.info(f"Winner: {winner.name}")
        winner.update_chef_stats('win')
        self.clear_kitchen
        
        return winner
    
    def clear_kitchen(self):
        if not self.kitchen:
            logger.warning("Attempted to clear an empty kitchen.")
            return
        logger.info("Clearing the chefs from the kitchen.")
        self.kitchen.clear()
    
    def enter_kitchen(self, chef_id: int):
        if len(self.kitchen) > 20:
            logger.error(f"Attempted to add Chef {chef_id} but too many cooks in the kitchen")
            raise ValueError("Kitchen is full")

        try:
            chef = Chef.get_chef_by_id(chef_id)
        except ValueError as e:
            logger.error(str(e))
            raise
        
        logger.info(f"Adding chef '{chef.name}' (ID {chef_id}) to the kitchen")

        
    def get_chefs(self):
        if not self.kitchen:
            logger.warning("Retreiving no chefs from an empty kitchen")
        else:
            logger.info(f"Retrieving {len(self.kitchen)} chefs from the kitchen")
            
        chefs_present: List[str] = []
        now = time.time()
        
        for chef_id in self.kitchen:
            if chef_id not in self._chefs_cache.keys or self._ttl.get(chef, 0) <= now:
                logger.info(f"TTL expired or missing for chef {chef_id}. Refreshing from DB.")
                chef = Chef.get_chef_by_id(chef_id)
                self._chefs_cache[chef_id] = chef
                self._ttl[chef_id] = now + self.ttl_seconds
            else:
                chef = self._chefs_cache.get(chef_id)
            chefs_present.append(chef)
            
        logger.info(f"Retrieved {len(chefs_present)} chefs from the kitchen: {chefs_present}")
        return chefs_present     
    
    def calculate_chef_skill(self, chef: Chef, cuisine: str) -> float:
        assert cuisine in self.cuisines
        logger.info(f"calculating skill level for chef: {chef.name} (ID {chef.id})")
        
        specialty_bonus = 5 if cuisine == chef.specialty else 0
        age_modifier = -5 if (chef.age < 25 and chef.years_experience < 4) or (chef.age > 55) else 0
        skill = (
            chef.years_experience * 4 +
            chef.signature_dishes * 2 + 
            specialty_bonus +
            age_modifier
        )
        
        logger.info(f"Skill level for {chef.name}: {skill:.3f}")
        return skill
    
    def clear_cache(self):
        """Clears the local TTL cache of chef objects.
        """
        logger.info("Clearing local chef cache in KitchenModel.")
        self._chefs_cache.clear()
        self._ttl.clear()