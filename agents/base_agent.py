class BaseAgent:
  def __init__(self, pref_manager):
      self.pref_manager = pref_manager
      self.confidence_threshold = 0.85
      self.learning_rate = 0.1

  def get_preference(self, context):
      """Get preference value for this agent's context"""
      return self.pref_manager.get_preference(self.__class__.__name__, context)

  def update_preference(self, context, feedback):
      """Update preference based on expert feedback"""
      return self.pref_manager.update_preference(
          self.__class__.__name__, 
          context, 
          feedback
      )