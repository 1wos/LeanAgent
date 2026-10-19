by
  intro hu hi
  have lu := UpdateStatesLength hu
  have li := InitStatesLength hi
  refine ⟨_, rfl, updatedStatesInit li
    (UpdateStatesNotDefMonotone' (InitStatesNotDefined hi) hu) (InitStatesNodup hi), ?_⟩
  rw [InitStatesUpdated hi, UpdateStatesUpdated hu]
  unfold updatedStates
  rw [updatedStatesComm]
  · exact updatedStatesUpdate lu
      (updatedStatesDefMonotone (UpdateStatesDefined' hu))
  · rw [List.unzip_zip lu, List.unzip_zip li]
    intro x hx hx'
    simpa [InitStatesNotDefined hi x hx'] using UpdateStatesDefined hu x hx
