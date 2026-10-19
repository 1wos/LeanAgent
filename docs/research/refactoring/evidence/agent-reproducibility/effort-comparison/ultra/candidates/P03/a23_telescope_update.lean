by
  intro hup hi
  have lu := UpdateStatesLength hup
  have li := InitStatesLength hi
  refine ⟨_, rfl, updatedStatesInit li (UpdateStatesNotDefMonotone' (InitStatesNotDefined hi) hup) (InitStatesNodup hi), ?_⟩
  cases InitStatesUpdated hi
  cases UpdateStatesUpdated hup
  unfold updatedStates
  rw [updatedStatesComm]
  · apply updatedStatesUpdate lu
    apply updatedStatesDefMonotone
    exact UpdateStatesDefined' hup
  · rw [List.unzip_zip lu, List.unzip_zip li]
    intro k hk hk'
    simpa [InitStatesNotDefined hi k hk'] using UpdateStatesDefined hup k hk
