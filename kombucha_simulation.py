import numpy as np
import math

class KombuchaSimulation:
    """
    Simulation model for kombucha fermentation and SCOBY's protective mechanisms against contaminants.
    """
    
    def __init__(self):
        # Initial values
        self.time = 0.0
        self.scoby_size = 1.0  # Initial SCOBY size (arbitrary units)
        self.pH = 4.2          # Initial pH
        self.oxygen = 1.0      # Initial oxygen level (normalized 0-1)
        self.bacteria = 1.0    # Initial beneficial bacteria population
        self.yeast = 1.0       # Initial beneficial yeast population
        self.contaminants = {} # Dictionary to store contaminant populations
        
        # Constants for differential equations
        self.dt = 1.0          # Time step for simulation
        
        # SCOBY growth parameters
        self.r_scoby = 0.15     # SCOBY growth rate
        self.K_scoby = 10.0    # SCOBY carrying capacity
        
        # pH parameters
        self.k_pH = 0.015       # Rate of pH decrease
        self.min_pH = 2.5      # Minimum possible pH
        
        # Oxygen parameters
        self.k_oxygen = 0.1    # Rate of oxygen consumption
        
        # Bacteria parameters
        self.r_bacteria = 0.3  # Bacteria growth rate
        self.K_bacteria = 8.0  # Bacteria carrying capacity
        
        # Yeast parameters
        self.r_yeast = 0.2     # Yeast growth rate
        self.K_yeast = 6.0     # Yeast carrying capacity
        
        # Contaminant parameters
        self.contaminant_types = {
            "mold": {
                "growth_rate": 0.5,
                "pH_threshold": 3.8,     # Most molds struggle below pH 3.8
                "oxygen_threshold": 0.4,  # Molds need significant oxygen
                "is_aerobic": True,
                "death_threshold_pH": 3.2 # pH below which mold starts dying
            },
            "harmful_bacteria": {
                "growth_rate": 0.3,
                "pH_threshold": 3.2,      # More acid-tolerant than mold but still limited
                "oxygen_threshold": 0.2,   # Can survive in lower oxygen
                "is_aerobic": False,
                "death_threshold_pH": 2.8  # pH below which harmful bacteria start dying
            }
        }
        
        # Physical barrier parameter (S_half in P_block equation)
        self.S_half = 2.0
        
        # History for plotting
        self.history = {
            'time': [self.time],
            'scoby_size': [self.scoby_size],
            'pH': [self.pH],
            'oxygen': [self.oxygen],
            'bacteria': [self.bacteria],
            'yeast': [self.yeast],
            'contaminants': {}
        }
    
    def reset(self):
        """Reset the simulation to initial values."""
        self.__init__()
        return self.get_state()
    
    def get_state(self):
        """Return the current state of the simulation."""
        state = {
            'time': self.time,
            'scoby_size': self.scoby_size,
            'pH': self.pH,
            'oxygen': self.oxygen,
            'bacteria': self.bacteria,
            'yeast': self.yeast,
            'contaminants': self.contaminants,
            'history': self.history
        }
        return state
    
    def g_pH(self, pH, threshold, is_beneficial=True):
        """
        Growth factor based on pH.
        Beneficial organisms thrive in lower pH, contaminants prefer higher pH.
        When pH is extremely unfavorable, returns negative values to model population decline.
        """
        if is_beneficial:
            # Beneficial organisms prefer lower pH
            if pH <= threshold:
                return 1.0
            else:
                return max(0.2, 1.0 - 0.3 * (pH - threshold))
        else:
            # Contaminants prefer higher pH
            if pH <= threshold - 0.5:  # Well below threshold - actively harmful
                return -0.2  # Negative growth factor indicates population decline
            elif pH <= threshold:      # Below threshold but not severely
                return 0.1   # Minimal but not negative growth
            else:
                # Above threshold - favorable conditions
                return min(1.0, 0.2 + 0.8 * (pH - threshold) / (7.0 - threshold))
    
    def g_oxygen(self, oxygen, threshold, is_aerobic):
        """
        Growth factor based on oxygen level.
        Aerobic organisms need oxygen, anaerobic can survive with less.
        """
        if is_aerobic:
            # Aerobic organisms need oxygen
            return 0.1 if oxygen < threshold else min(1.0, 0.1 + 0.9 * (oxygen - threshold) / (1.0 - threshold))
        else:
            # Anaerobic organisms prefer low oxygen
            return 0.8 if oxygen < threshold else max(0.2, 0.8 - 0.6 * (oxygen - threshold) / (1.0 - threshold))
    
    def introduce_contaminant(self, contaminant_type):
        """
        Attempt to introduce a contaminant. The SCOBY may block it based on its size.
        Returns a message about what happened.
        """
        if contaminant_type not in self.contaminant_types:
            return f"Error: Unknown contaminant type '{contaminant_type}'"
        
        # Physical barrier mechanism
        # Probability that contaminant is blocked by SCOBY
        p_block = self.scoby_size / (self.scoby_size + self.S_half)
        blocked = np.random.random() < p_block
        
        message = ""
        if blocked:
            message = f"{contaminant_type.capitalize()} was blocked by the SCOBY physical barrier!"
        else:
            # Initialize contaminant with a small population
            self.contaminants[contaminant_type] = 0.5
            if contaminant_type not in self.history['contaminants']:
                self.history['contaminants'][contaminant_type] = [0.0] * len(self.history['time'])
                # Fill history with zeros up to current time
                self.history['contaminants'][contaminant_type][-1] = 0.5
            message = f"{contaminant_type.capitalize()} has entered the kombucha! Initial population: 0.5"
        
        return message
    
    def step(self, steps=1):
        """Advance the simulation by n time steps."""
        for _ in range(steps):
            # Update time
            self.time += self.dt
            
            # Calculate growth factors for beneficial organisms
            bacteria_g_pH = self.g_pH(self.pH, 3.0, is_beneficial=True)
            bacteria_g_oxygen = self.g_oxygen(self.oxygen, 0.3, is_aerobic=False)
            
            yeast_g_pH = self.g_pH(self.pH, 3.2, is_beneficial=True)
            yeast_g_oxygen = self.g_oxygen(self.oxygen, 0.5, is_aerobic=True)
            
            # Update SCOBY size (logistic growth)
            dscoby = self.r_scoby * self.scoby_size * (1 - self.scoby_size / self.K_scoby) * self.dt
            self.scoby_size += dscoby
            
            # Update pH (decreases due to acid production)
            dpH = -self.k_pH * (self.scoby_size + self.bacteria) * self.dt
            self.pH = max(self.min_pH, self.pH + dpH)
            
            # Update oxygen (consumed by organisms)
            doxygen = -self.k_oxygen * (self.scoby_size + self.bacteria + self.yeast) * self.dt
            self.oxygen = max(0.0, self.oxygen + doxygen)
            
            # Update beneficial bacteria (now using logistic growth)
            dbacteria = self.r_bacteria * self.bacteria * (1 - self.bacteria / self.K_bacteria) * bacteria_g_pH * bacteria_g_oxygen * self.dt
            self.bacteria += dbacteria
            
            # Update beneficial yeast (now using logistic growth)
            dyeast = self.r_yeast * self.yeast * (1 - self.yeast / self.K_yeast) * yeast_g_pH * yeast_g_oxygen * self.dt
            self.yeast += dyeast
            
            # Update contaminants with realistic decline in unfavorable conditions
            to_remove = []
            for contaminant_type, population in self.contaminants.items():
                params = self.contaminant_types[contaminant_type]
                
                # Calculate growth factors
                pH_factor = self.g_pH(self.pH, params["pH_threshold"], is_beneficial=False)
                oxygen_factor = self.g_oxygen(self.oxygen, params["oxygen_threshold"], params["is_aerobic"])
                
                # Competitive exclusion effect (simplified)
                competition_factor = 1.0 / (1.0 + 0.1 * (self.bacteria + self.yeast))
                
                # Determine if conditions are highly unfavorable
                highly_unfavorable = False
                
                # For mold: highly unfavorable if pH is very low OR oxygen is depleted
                if contaminant_type == "mold":
                    if self.pH < (params["pH_threshold"] - 0.5) or (params["is_aerobic"] and self.oxygen < 0.1):
                        highly_unfavorable = True
                
                # For harmful bacteria: highly unfavorable if pH is very low
                elif contaminant_type == "harmful_bacteria":
                    if self.pH < (params["pH_threshold"] - 0.3):
                        highly_unfavorable = True
                
                # Update population with realistic decline in unfavorable conditions
                if highly_unfavorable:
                    # Apply a negative growth rate (population decline) when conditions are highly unfavorable
                    decline_rate = -0.05 * population  # Organisms die off at a rate proportional to population
                    population += decline_rate * self.dt
                else:
                    # Normal growth calculation when conditions aren't highly unfavorable
                    growth_rate = params["growth_rate"] * pH_factor * oxygen_factor * competition_factor
                    dpop = growth_rate * population * self.dt
                    population += dpop
                
                # Check if population is too small (effectively extinct)
                if population < 0.01:
                    to_remove.append(contaminant_type)
                    population = 0.0
                
                self.contaminants[contaminant_type] = population
            
            # Remove extinct contaminants
            for contaminant_type in to_remove:
                del self.contaminants[contaminant_type]
            
            # Update history
            self.history['time'].append(self.time)
            self.history['scoby_size'].append(self.scoby_size)
            self.history['pH'].append(self.pH)
            self.history['oxygen'].append(self.oxygen)
            self.history['bacteria'].append(self.bacteria)
            self.history['yeast'].append(self.yeast)
            
            # Update contaminant history
            for contaminant_type in self.contaminant_types:
                if contaminant_type not in self.history['contaminants']:
                    self.history['contaminants'][contaminant_type] = [0.0] * len(self.history['time'])
                else:
                    # Ensure history length matches
                    while len(self.history['contaminants'][contaminant_type]) < len(self.history['time']):
                        self.history['contaminants'][contaminant_type].append(0.0)
                
                if contaminant_type in self.contaminants:
                    self.history['contaminants'][contaminant_type][-1] = self.contaminants[contaminant_type]
        
        return self.get_state()