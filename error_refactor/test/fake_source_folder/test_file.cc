#include <Data.hh>
#include <UtilityFunctions.hh>

void nothing_to(void * see_here) {
    // must error
    ShowSevereError(state, "Something Bad");
    ShowContinueError(state, "Happened Here!");  // error here
    int x = 1;
    ShowContinueError(state,
        format(
            "It might be this: {} or that: {}",
            state.data->Node(1).Temp,
            state.data->CoolVector[x].attributeY
        )
    );
    ShowFatalError(state, "Can't go on...");
}
