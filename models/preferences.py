class PreferenceManager:
  def __init__(self, database):
      self.db = database
      self.cache = {}

  def update_preference(self, agent_type, context, feedback_value):
      """Update preference with new feedback"""
      current_value = self.get_preference(agent_type, context)
      learning_rate = 0.1  # Can be adjusted

      new_value = (1 - learning_rate) * current_value + learning_rate * feedback_value
      self.db.save_preference(agent_type, context, new_value)
      self.cache[(agent_type, context)] = new_value

      return new_value

  def get_preference(self, agent_type, context):
      """Get current preference value"""
      cache_key = (agent_type, context)

      if cache_key not in self.cache:
          self.cache[cache_key] = self.db.get_preference(agent_type, context)

      return self.cache[cache_key]

  def clear_cache(self):
      """Clear the preference cache"""
      self.cache = {}